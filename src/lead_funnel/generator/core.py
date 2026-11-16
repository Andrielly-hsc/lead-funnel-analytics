"""Orchestration of a full generator run: ``generate(params, seed)``.

Each stage receives its **own** random generator, spawned from one seed with
``numpy.random.SeedSequence``. The stages are therefore statistically independent,
and changing one stage (say, a new interaction type) leaves the random draws of
every other stage untouched.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from lead_funnel.generator import corruption, entities, funnel
from lead_funnel.generator.params import GeneratorParams, to_dict
from lead_funnel.generator.schema import ENTITIES

logger = logging.getLogger(__name__)

# order matters: appending a new stage at the end keeps all existing streams stable
STAGES = (
    "agents",
    "campaigns",
    "leads",
    "routing",
    "first_response",
    "conversion",
    "opportunities",
    "interactions",
    "corrupt_leads",
    "corrupt_interactions",
)


@dataclass
class GeneratedData:
    """Result of one run: the source tables plus everything only the generator knows."""

    tables: dict[str, pd.DataFrame]
    truth_leads: pd.DataFrame  # per-lead true values (never visible in a real CRM)
    ground_truth: dict  # parameters, realised effects and the injection log


def generate(
    params: GeneratorParams | None = None, seed: int = 42, *, clean: bool = False
) -> GeneratedData:
    """Run the whole simulation. ``clean=True`` skips the injection of quality issues."""
    gp = params or GeneratorParams()
    rngs = dict(
        zip(
            STAGES,
            (np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(len(STAGES))),
            strict=True,
        )
    )
    tz = gp.volume.timezone

    agents = entities.make_agents(gp, rngs["agents"])
    campaigns = entities.make_campaigns(gp, rngs["campaigns"])
    leads = entities.make_leads(gp, rngs["leads"], campaigns)
    leads["owner_agent_id"] = entities.assign_agents(leads, agents, rngs["routing"], tz)
    team = entities.routed_team(leads)

    response = funnel.simulate_first_response(leads, agents, team, gp, rngs["first_response"])
    conversion = funnel.simulate_conversion(leads, response, gp, rngs["conversion"])
    opportunities = funnel.simulate_opportunities(
        leads, response, conversion, gp, rngs["opportunities"]
    )
    interactions = funnel.simulate_interactions(
        leads, response, conversion, opportunities, gp, rngs["interactions"]
    )
    truth = funnel.summarise_truth(response, conversion)
    logger.info(
        "Simulated %d leads: naive SLA gap %.1f pp vs true effect %.1f pp",
        truth["n_leads"],
        truth["naive_sla_gap_pp"],
        truth["true_effect_on_leads_missing_sla_pp"],
    )

    truth_leads = pd.DataFrame(
        {
            "lead_id": leads["lead_id"],
            "routed_team": team,
            "size_band": entities.size_band(leads["company_size"]),
            "true_company_size": leads["company_size"],
            "true_channel": leads["channel"],
            "true_country": leads["country"],
            "responded": response["responded"],
            "true_first_response_at": response["first_response_at"],
            "true_hours_to_first_response": response["hours_to_first_response"],
            "p_conversion": conversion["p_conversion"],
            "p_conversion_policy": conversion["p_conversion_policy"],
            "converted": conversion["converted"],
        }
    )

    log = corruption.InjectionLog()
    if not clean:
        corrupted_leads = corruption.corrupt_leads(leads, gp.corruption, rngs["corrupt_leads"], log)
        interactions = corruption.corrupt_interactions(
            interactions, leads, gp.corruption, rngs["corrupt_interactions"], log
        )
        leads = corrupted_leads
        logger.info("Injected quality issues: %s", log.counts)

    tables = {
        "leads": leads,
        "interactions": interactions,
        "agents": agents,
        "campaigns": campaigns,
        "opportunities": opportunities,
    }
    tables = {name: df[ENTITIES[name].column_names] for name, df in tables.items()}
    ground_truth = {
        "seed": seed,
        "clean": clean,
        "params": to_dict(gp),
        "realised": truth,
        "injected_issues": log.to_dict(),
    }
    return GeneratedData(tables=tables, truth_leads=truth_leads, ground_truth=ground_truth)
