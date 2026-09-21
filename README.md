# Toy Story (Mega Drive) — disassembly pass

Static analysis only (per the smd-disassembly skill: mapping, not a patched
ROM). Start with `log/toystory-notes.md` for the narrative, `log/toystory_facts.py`
for the structured per-game facts, `traces/trace_eu_pal.json` for the raw
recursive-descent trace (EU/PAL ROM), and `scripts/` for the tools used to
produce all of it (rebuilt from scratch this session — see the notes file for why).

Rerun the tracer with extra manual seeds as:

    python3 scripts/trace.py "Toy Story (Europe).gen" out.json <hex_addr> [<hex_addr> ...]

---

## See it in action

See what mods Pluto has helped me build from disassemblies like this one, with gameplay on real hardware:

- 📸 **Instagram:** [@consolesplayingconsoles](https://www.instagram.com/consolesplayingconsoles/)
- 🔗 **Everything else:** [beacons.ai/consolesplayingconsoles](https://beacons.ai/consolesplayingconsoles)
