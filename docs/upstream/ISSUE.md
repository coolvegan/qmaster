# Upstream issue draft — program/preset changes do not refresh the MPC editor

Status: **draft, not submitted.** No hardware verification yet.

## Summary

With the SDK framework, selecting a built-in program (`effSetProgram`) or
restoring a project/preset chunk (`effSetChunk`) changes every parameter inside
the plugin, but the MPC keeps showing the previous knob positions. The values
are correct; only the display is stale until the user touches a control.

## Minimal reproduction

1. Build any SDK effect with at least two programs whose values differ, e.g.
   QVerb `Vocal Air` and `Hazy Pad` (or a two-parameter test plugin).
2. Load it on an MPC (OS 3.10.1+, External Plugin Support on).
3. Select program 1 from the preset selector.
4. Observe: audio changes, the parameter values on screen do not.

`host_sim` confirms the call counts: before any change the plugin emits
`audioMasterAutomate 0` and `audioMasterUpdateDisplay 0` during the load and
program selection sequence. The host calls `effSetProgram` and then reads the
parameter values only when it decides to repaint.

## Current local workaround

In the vendored `framework/mpc_plugin.h`, after the parameter loop in
`setProgram()` and at the end of `internalLoadState()`:

```cpp
for (int i = 0; i < numParams(); ++i)
    notifyHostParameterChanged(i);
requestDisplayUpdate();
```

This makes the editor follow the preset. It is not upstream. With QDelay's 38
parameters it is 38 automate calls plus one display update per program/chunk
load, on the UI thread, for every instance.

## Why this is only a draft

- `audioMasterAutomate` means “a parameter moved” (automation), not “state was
  restored”. Calling it inside `effSetChunk`/`effSetProgram` may mark the
  project dirty, write automation or re-enter host UI logic.
- `host_sim` counts the callbacks but does not simulate re-entrancy.
- No MPC hardware test has been done for the upstream patch, and
  `CONTRIBUTING.md` asks for the model/firmware used.

## Questions for the maintainers

1. Is the stale editor after `effSetProgram`/`effSetChunk` a known host
   limitation, or should the plugin request a redraw?
2. Is `requestDisplayUpdate()` alone sufficient on the device, without the
   per-parameter `audioMasterAutomate` calls?
3. If automate calls are needed, should they be limited to parameters that
   actually changed, deferred to idle, or guarded against re-entry?
4. Would a host-sim test that fails on re-entrant callbacks be accepted?

## Suggested minimal fix

Start with `requestDisplayUpdate()` after program/chunk load; keep the
per-parameter notifications only if the device needs them, and guard them
against re-entry. The local patch is in
`docs/upstream/notify-host-on-program-change.patch` for reference.

## Environment

- SDK commit `e78bad5` (23.11.2026)
- MPC OS 3.10.1, External Plugin Support
- Plugins: QMaster, QVerb, QDelay, QDSSD
- Host simulator: 20/20 / 19/19 passes, automate/update counts measured
