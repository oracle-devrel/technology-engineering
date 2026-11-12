"""Authorization is evaluated by application code, independently of the model."""
import re
from datetime import datetime, timezone, timedelta


class PolicyError(ValueError):
    pass


class QueryValidationError(PolicyError):
    """Correctable Log Analytics syntax, distinct from an authorization denial."""


class ToolPrerequisiteError(PolicyError):
    """A missing discovery step; correcting it does not relax authorization."""


def allowed_environments(policy, user):
    groups = set(user.get("groups", []))
    return {key: env for key, env in policy["environments"].items()
            if groups.intersection(env.get("groups", [])) or user["sub"] in env.get("subjects", [])}


def authorize_environment(policy, user, key):
    env = allowed_environments(policy, user).get(key)
    if not env:
        raise PolicyError("You do not have access to that environment")
    if not env.get("compartment_id", "").startswith("ocid1.compartment."):
        raise PolicyError("The environment has no configured compartment OCID")
    return env


def environment_options(policy, user):
    """Expose hierarchy only among this user's approved environments."""
    allowed=allowed_environments(policy,user)
    by_compartment={v['compartment_id']:key for key,v in allowed.items()}
    parents={key:by_compartment.get(v.get('parent_compartment_id')) for key,v in allowed.items()}
    # Bad administrative metadata must not hide a selectable environment in a cycle.
    for key in parents:
        seen={key};cursor=parents[key]
        while cursor is not None:
            if cursor in seen:
                parents[key]=None;break
            seen.add(cursor);cursor=parents.get(cursor)
    return [{'id':key,'label':v['label'],'compartment_id':v['compartment_id'],'parent_id':parents[key],
        'available_mcps':list(v.get('connection_refs',{'db':'builtin','logan':'builtin'}))} for key,v in allowed.items()]


def timestamps(hours):
    if not isinstance(hours, int) or not 1 <= hours <= 168:
        raise PolicyError("Choose a window from 1 to 168 hours")
    end = datetime.now(timezone.utc) - timedelta(seconds=5)
    # Database Management accepts millisecond UTC windows, not microseconds.
    return ((end - timedelta(hours=hours)).isoformat(timespec='milliseconds'), end.isoformat(timespec='milliseconds'))


def bound_arguments(args, compartment, properties):
    """Scope only schema-supported arguments; reject conflicting nested scope."""
    out = dict(args)
    def check(value):
        if isinstance(value, dict):
            for key, val in value.items():
                if key in {"compartment_id", "compartmentId"} and val != compartment:
                    raise PolicyError("Cross-compartment access is blocked")
                if key in {"compartment_id_in_subtree", "include_subcompartments", "include_sub_compartments"} and val:
                    raise PolicyError("Subcompartments are outside this environment")
                if key in {"scope", "query_scope"} and val not in {"default", None}:
                    raise PolicyError("Tenancy queries are blocked")
                check(val)
        elif isinstance(value, list):
            for v in value:
                check(v)
    check(out)
    if "compartment_id" in properties:
        out["compartment_id"] = compartment
    for k in ("compartment_id_in_subtree", "include_subcompartments"):
        if k in properties:
            out[k] = False
    return out


def safe_query(query):
    if not isinstance(query, str) or not 1 <= len(query) <= 6000:
        raise QueryValidationError("Use a Log Analytics query of 1 to 6000 characters.")
    if re.match(r'(?is)^\s*SELECT\b', query):
        raise QueryValidationError('Use Log Analytics pipelines, not SELECT/FROM SQL. Example: * | stats count as Records by \'Log Source\', Entity')
    # Read-oriented Logan pipelines only; disallow exporting, executing or writing.
    allowed = {"stats", "fields", "head", "sort", "where", "eval", "cluster", "timestats", "dedup", "rename", "top", "bottom"}
    stages, start, quote, escaped = [], 0, None, False
    for index, char in enumerate(query):
        if escaped:
            escaped = False
        elif quote and char == '\\':
            escaped = True
        elif quote:
            if char == quote:
                quote = None
        elif char in {'"', "'"}:
            quote = char
        elif char == '|':
            stages.append(query[start:index]); start = index + 1
    if quote:
        raise QueryValidationError('Close quoted field names and string values before submitting the query.')
    stages.append(query[start:])
    for stage in stages[1:]:
        words = stage.split(None, 1)
        word = words[0].lower() if words else ''
        if word == 'stats' and re.search(r'(?i)(?:^\s*stats\s+|,\s*)count\s*\(\s*\)', stage):
            raise QueryValidationError('Log Analytics uses stats count, not count(). Use: * | stats count as Records')
        if word not in allowed:
            raise QueryValidationError('Use a supported read-only pipeline stage: '+', '.join(sorted(allowed))+'. Use head 10 rather than limit 10.')
    return query


def redact(text):
    text = re.sub(r"(?i)([?&](?:code|state|access_token|id_token|client_secret)=)[^&\s\"']+", r"\1[REDACTED]", str(text))
    text = re.sub(r"eyJ[A-Za-z0-9_.-]{30,}", "[REDACTED TOKEN]", text)
    text = re.sub(r"(?i)(authorization\s*[:=]\s*(?:bearer|datakey)\s+)\S+", r"\1[REDACTED]", text)
    return text
