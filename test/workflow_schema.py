"""What inputs a ComfyUI node actually requires, dotted children included.

New-schema nodes (COMFY_DYNAMICCOMBO_V3) do not take a nested object in
API-format JSON. Choosing an option pulls that option's own required inputs
into the SAME flat inputs dict under a dot-joined name - so BuildPoseFile with
format=glb and mesh_style=body_mesh requires 'format.mesh_style.bone_vis' as a
top-level key. Passing a nested dict validates and then fails at execution
with 'missing 1 required positional argument', which is a long way from the
mistake.

This walks the option tree the way the server does, so the test built on it
fails the moment a ComfyUI update adds, renames or re-nests a child input -
the likeliest thing about these two workflows to rot.
"""
import json
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8000"


def object_info(class_type, base=DEFAULT_BASE, timeout=15):
    """One node's schema, or None when the server is not there.

    Per-node rather than the whole /object_info: the full document is large
    enough that reading it has been seen to reset the connection.
    """
    try:
        url = "%s/object_info/%s" % (base.rstrip("/"), class_type)
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8")).get(class_type)
    except Exception:
        return None


def server_is_up(base=DEFAULT_BASE, timeout=2.0):
    try:
        urllib.request.urlopen(base.rstrip("/") + "/system_stats", timeout=timeout)
        return True
    except Exception:
        return False


def expected_inputs(required, values, prefix=""):
    """Every input key `required` demands, given the values already chosen.

    `values` is the node's own flat inputs dict from the workflow JSON - the
    walk is value-directed because which children exist depends on which
    option was picked.
    """
    out = []
    for name, definition in required.items():
        key = prefix + name
        out.append(key)
        if definition[0] != "COMFY_DYNAMICCOMBO_V3":
            continue
        meta = definition[1] if len(definition) > 1 else {}
        chosen = values.get(key)
        for option in meta.get("options", []):
            if option["key"] == chosen:
                out += expected_inputs(
                    option.get("inputs", {}).get("required", {}), values, key + ".")
                break
    return out


def dynamic_combo_choices(required, values, prefix=""):
    """(key, chosen value, legal keys) for every COMFY_DYNAMICCOMBO_V3 field.

    A COMFY_DYNAMICCOMBO_V3's own options never show up in the plain-COMBO
    branch of a value-membership check - its kind is the literal string
    "COMFY_DYNAMICCOMBO_V3", not a list of choices and not "COMBO", so a
    check that only handles those two shapes silently skips it. This walks
    the same option tree expected_inputs() does (a chosen option's own
    dynamic-combo children are just as much a COMFY_DYNAMICCOMBO_V3 as the
    top-level field is - format.mesh_style nested inside format="glb", for
    instance), but returns what a value check needs instead of a flat key
    list: the key, whatever the workflow actually chose, and the legal keys
    the live server offers for it.
    """
    out = []
    for name, definition in required.items():
        key = prefix + name
        if definition[0] != "COMFY_DYNAMICCOMBO_V3":
            continue
        meta = definition[1] if len(definition) > 1 else {}
        options = meta.get("options", [])
        chosen = values.get(key)
        out.append((key, chosen, [option["key"] for option in options]))
        for option in options:
            if option["key"] == chosen:
                out += dynamic_combo_choices(
                    option.get("inputs", {}).get("required", {}), values, key + ".")
                break
    return out
