# Demo Script

## Goal

Show perception, reasoning, and human oversight together in under a minute — don't read
a feature list, walk one scenario live.

## Pre-demo checklist (do this before judges arrive)

- [ ] Backend running, `/health` returns ok
- [ ] Perception running on the prepared sample video, console showing periodic logs
- [ ] Dashboard open, connected (check WebSocket status indicator)
- [ ] `ANTHROPIC_API_KEY` valid and backend restarted recently (avoid stale/expired key)
- [ ] Venue wifi confirmed working, or hotspot ready as backup (agent needs internet)
- [ ] Zones defined and tested against this specific video — occupancy gauges showing
      sensible numbers, not all zeros or garbage
- [ ] Volume/screen visible from judge seating distance

## The scenario (~45 seconds)

**Setup line:** "It's exam day at Gate 3. Watch what happens when a bag gets left
behind."

1. **[0:00]** Point at the live feed panel — bounding boxes visible on people/objects in
   real time. *"This is real detection running now, not a recorded clip."*

2. **[0:05]** A bag is left unattended in the video. Dwell timer starts.

3. **[0:30]** Dwell threshold crosses — a **low-priority** alert appears in the list.
   *"The system noticed a stationary bag, but hasn't panicked yet."*

4. **[0:35]** The same tracked person is seen moving away quickly on a second event.
   *"Now watch — the agent is connecting this to the earlier bag."*

5. **[0:40]** Alert escalates to **high-priority**, notification draft appears.
   *"It correlated two separate detections and re-prioritized on its own."*

6. **[0:45]** Click the alert, show the "why flagged" explanation.
   *"This isn't a black box — it explains its reasoning, and this text was already
   computed, so it's instant."*

7. **[0:50]** Click "Acknowledge" as the operator.
   *"A human is always the one who closes the loop — the AI recommends, it doesn't
   act alone."*

## Backup talking points if something breaks live

- **Agent call fails/times out:** *"This is actually one of our design decisions — if
  the LLM is unavailable, the system falls back to a deterministic severity rule
  automatically, so it never goes silent."* (Then show a fallback-triggered incident if
  one is on screen.)
- **Detection looks shaky:** *"We're running the small/fast YOLO variant for real-time
  demo speed — the architecture supports swapping in a larger model for production
  accuracy without any other changes."*
- **Wifi drops:** pivot to the pre-recorded demo video (always have one ready, see
  below).

## Always have a backup: pre-recorded demo video

Record a clean run-through of the exact scenario above beforehand. If live demo fails
for any reason, play the video and narrate over it — judges care more about seeing the
concept work than watching you debug live.

## Closing line

*"Everything you just saw — detection, tracking, reasoning, and the human checkpoint —
runs locally except for one LLM call, which means this is genuinely deployable on
campus edge hardware with only structured incident data ever leaving the building."*

## Questions judges commonly ask (be ready)

- **"How accurate is the detection?"** — Be honest: pretrained YOLO on COCO, not
  fine-tuned on campus-specific footage. State this as a known limitation and a clear
  next step (collect campus CCTV data, fine-tune).
- **"What if the agent hallucinates a threat?"** — Explain the boundary: the agent only
  reasons over facts the CV layer already confirmed, it never sees raw video, and the
  system prompt explicitly instructs it to lower severity rather than guess high when
  uncertain.
- **"Does this scale to real campus deployment?"** — Point to the architecture's
  edge-deployment design (Jetson-class devices per camera, only structured incidents
  crossing the network) even though the demo runs on laptops.
- **"What about privacy?"** — The agent never processes raw video or biometric data,
  only structured detection facts; no face recognition is used in this system.
