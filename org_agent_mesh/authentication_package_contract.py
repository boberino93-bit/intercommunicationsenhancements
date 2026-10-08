from __future__ import annotations

from typing import Mapping, Any


HIGH = {
    "ROOT_AUTHORITY_CHANGE",
    "UNIVERSAL_GOVERNANCE_CHANGE",
    "PRODUCTION_PROMOTION_OR_DEPLOYMENT",
    "SECURITY_OR_CREDENTIAL_BOUNDARY_CHANGE",
    "FINANCIAL_EFFECT",
    "DESTRUCTIVE_OR_IRREVERSIBLE_OPERATION",
    "SCHEDULE_ENABLE_OR_REENABLE",
    "CROSS_PROJECT_MUTATION",
}

REQUIRED_COMPONENT_PATTERNS = {
    "AGENT_BOOTSTRAP.json",
    "BOOTSTRAP_ORDER.json",
    "governance/*.json",
    "protocols/*.md",
    "org_agent_mesh/*.py",
    "schemas/*.json",
    "templates/new-project/*.json",
    "governance/AUTHENTICATION_FACTOR_POLICY.json",
    "protocols/authentication_factor_gateway.md",
    "org_agent_mesh/authentication_gateway.py",
    "org_agent_mesh/authentication_package_contract.py",
    "schemas/authentication_attestation.schema.json",
}


def validate_factor_policy(policy: Mapping[str, Any]) -> None:
    if policy.get("schema") != "org-agent-mesh/authentication-factor-policy/v2":
        raise ValueError("unsupported authentication factor policy schema")
    if policy.get("presence") != "MANDATORY_IN_EVERY_BOOTSTRAP_PACKAGE":
        raise ValueError("authentication factor policy is not mandatory in every package")
    if policy.get("enforcement_point") != "BEFORE_PROTECTED_MUTATION_AUTHORIZATION":
        raise ValueError("authentication factor enforcement point is unsafe")
    if policy.get("read_only_boot_without_human_challenge") is not True:
        raise ValueError("read-only bootstrap must remain autonomous")
    if policy.get("fail_closed") is not True:
        raise ValueError("authentication factor policy must fail closed")

    factors = policy.get("factors", {})
    totp = factors.get("baseline", {})
    if totp.get("method") != "TOTP_RFC6238" or "PROTECTED_MUTATION" not in set(totp.get("required_for", [])):
        raise ValueError("mandatory TOTP baseline missing")
    if totp.get("secret_source") != "EXTERNAL_SECRET_RESOLVER_ONLY" or totp.get("inline_secret") != "DENY":
        raise ValueError("TOTP secret must be external and never inline")
    if totp.get("persist_or_log_secret") != "DENY":
        raise ValueError("TOTP secret persistence/logging must be denied")
    if totp.get("case_bound_attestation") is not True or totp.get("action_digest_binding") is not True:
        raise ValueError("TOTP attestation lacks case/action binding")
    if totp.get("replay_protection") != "MATCHED_COUNTER_SINGLE_USE":
        raise ValueError("TOTP matched-counter replay protection missing")

    microsoft = factors.get("tertiary", {})
    if microsoft.get("method") != "MICROSOFT_ENTRA_AUTHENTICATOR":
        raise ValueError("Microsoft Authenticator tertiary factor missing")
    if microsoft.get("integration") != "OIDC_OAUTH2_CONDITIONAL_ACCESS_AUTH_CONTEXT":
        raise ValueError("Microsoft Authenticator integration must use Entra OIDC/OAuth step-up")
    if microsoft.get("authentication_context_source") != "TENANT_CONFIGURATION_NOT_HARDCODED":
        raise ValueError("Entra authentication context must not be hard-coded")
    if microsoft.get("jwt_signature_issuer_audience_expiry_validation") != "REQUIRED_BEFORE_NORMALIZATION":
        raise ValueError("Microsoft token cryptographic validation is not mandatory")
    for key in ("principal_binding", "nonce_binding", "fresh_authentication_required", "token_replay_protection"):
        if microsoft.get(key) is not True:
            raise ValueError(f"Microsoft factor missing required control: {key}")

    sms = factors.get("fallback", {})
    if sms.get("method") != "SMS_OTP" or sms.get("assurance") != "RESTRICTED_FALLBACK":
        raise ValueError("SMS must remain a restricted fallback")
    if sms.get("store_plaintext_code") is not False:
        raise ValueError("SMS plaintext code storage must be disabled")
    if sms.get("single_use") is not True:
        raise ValueError("SMS code must be single-use")
    if int(sms.get("ttl_seconds", 9999)) > 300:
        raise ValueError("SMS TTL exceeds 300 seconds")
    if not (1 <= int(sms.get("max_attempts", 999)) <= 5):
        raise ValueError("SMS attempt limit is unsafe")
    if sms.get("high_consequence_independent_factor") is not False:
        raise ValueError("SMS must not be a high-consequence independent factor")

    strong = set(policy.get("strong_independent_methods", []))
    if strong != {"REGISTERED_GITHUB_EXTERNAL_CHALLENGE", "MICROSOFT_ENTRA_AUTHENTICATOR"}:
        raise ValueError("strong independent factor set drifted")
    if "SMS_OTP" in strong:
        raise ValueError("SMS incorrectly elevated to strong factor")
    if set(policy.get("high_consequence_classes", [])) != HIGH:
        raise ValueError("high consequence class coverage drift")
    expected_rule = "TOTP_RFC6238 AND (REGISTERED_GITHUB_EXTERNAL_CHALLENGE OR MICROSOFT_ENTRA_AUTHENTICATOR)"
    if policy.get("high_consequence_rule") != expected_rule:
        raise ValueError("high consequence authentication rule drift")

    secrets = policy.get("secrets", {})
    required_denials = {
        "totp_seed_in_repository_or_package",
        "sms_destination_in_repository_or_package",
        "sms_pepper_in_repository_or_package",
        "microsoft_client_secret_in_repository_or_package",
        "attestation_signing_key_in_repository_or_package",
    }
    for key in required_denials:
        if secrets.get(key) != "DENY":
            raise ValueError(f"secret packaging prohibition missing: {key}")


def validate_package_dependency_patterns(dependency_map: Mapping[str, Any]) -> None:
    patterns = set(dependency_map.get("shared_patterns", []))
    missing = REQUIRED_COMPONENT_PATTERNS - patterns
    if missing:
        raise ValueError("package dependency map omits auth-bearing components: " + ", ".join(sorted(missing)))
