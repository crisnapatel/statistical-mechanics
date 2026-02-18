# Statistical Mechanics — But Make It Make Sense

A conversational, no-nonsense walkthrough of statistical mechanics for people who learn better from YouTube than from textbooks.

**Live site**: [crisnapatel.github.io/statistical-mechanics](https://crisnapatel.github.io/statistical-mechanics/)

## What is this?

This project takes the content from Kerson Huang's *Statistical Mechanics* (2nd Edition) and re-explains it chapter by chapter in a conversational style inspired by creators like [NetworkChuck](https://www.youtube.com/@NetworkChuck) and [Theo (t3.gg)](https://www.youtube.com/@t3dotgg).

Where it helps, we run **actual MD simulations** (LAMMPS) to demonstrate the physics — not just equations, but real data from real systems.

## Who is this for?

- People doing MD simulations who want to understand the physics underneath
- Students who find textbook language hard to parse at normal reading speed
- Anyone who thinks "I'm not smart enough for this" (you are — the textbook just isn't talking to you)

## Books Used

1. **Primary**: Huang, Kerson. *Statistical Mechanics*. 2nd Edition, 1987.
2. **Companion**: Huang, Kerson. *Introduction to Statistical Physics*. 2nd Edition.

## Local Development

```bash
# Install (conda)
conda install -c conda-forge mkdocs-material

# Serve locally
mkdocs serve

# Deploy to GitHub Pages
mkdocs gh-deploy
```

## Contributing

Found a mistake? Think something could be explained better? Open an issue or PR.

## License

Content is shared under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
