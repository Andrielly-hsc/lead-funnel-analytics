{#-
    Pseudonymise a personal identifier with a salted SHA-256 hash.

    * The same input always gives the same hash, so records can still be joined
      and de-duplicated (useful), but the raw value cannot be read back.
    * The salt comes from the LF_HASH_SALT environment variable. Without a secret
      salt, anyone could hash a known e-mail and look it up (dictionary attack).
      The default is for local development only; set a real secret in production.
    * Pseudonymised data is still personal data under GDPR (Recital 26): it reduces
      risk, it does not anonymise.
-#}
{% macro pseudonymise(expression) -%}
    sha256('{{ env_var("LF_HASH_SALT", "local-dev-salt-not-secret") }}' || {{ expression }})
{%- endmacro %}
