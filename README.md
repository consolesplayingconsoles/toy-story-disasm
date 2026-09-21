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

## License

© 2026 consolesplayingconsoles. Free software under the **GNU General Public License v3.0 or later** ([GPL-3.0-or-later](LICENSE)): use it, study it, share it, modify it. Derivative works stay under the same licence, so what gets built on this stays open too.

This covers the tools and notes in this repo. It does not cover the original game, its ROM or its code, none of which are included.
