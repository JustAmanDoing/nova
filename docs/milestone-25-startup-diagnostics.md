# Milestone 25: Automatic startup diagnostics

## Outcome

Nova's Windows controller now shows useful local diagnostics automatically
when the production stack cannot be built or does not become ready.

## Behavior

After a failed Compose start or a 90-second readiness timeout, the controller
prints:

1. the current container state;
2. the most recent 80 lines from the backend and frontend container logs;
3. the original failure message.

The output is bounded so an old or noisy log cannot flood the terminal. It is
shown only on the local PC and does not upload logs or application data.

Stop, status, update, volume retention, and loopback-only networking behavior
remain unchanged.

## Verification

The Windows CI job parses the controller and verifies that the bounded
diagnostic path remains present alongside all four root launchers.
