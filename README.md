
<p align="center">
  <a href="https://github.com/nexios-labs">
    <img alt="Nexios Logo" height="350" src="https://nexios-docs.netlify.app/logo.png"> 
  </a>
</p>

<h1 align="center">Nexips Project Template</h1>


# Nexips Project Template

A simple project template for building packages under the [@nexios-labs](https://github.com/nexios-labs) organization.  
This template is powered by **[Nexios](https://nexios-docs.netlify.app/)** and uses **[uv](https://github.com/astral-sh/uv)** for dependency management.  
Documentation is built with **[VitePress](https://vitepress.dev/)**.  

---

## 🚀 Getting Started

1. **Use this template** on GitHub to create your new project.
2. Clone your new repository.
3. Install dependencies with:

```bash
   uv sync
````

4. Update `pyproject.toml` with:

   * Project name
   * Description
   * Author / Maintainer details
   * Dependencies

5. Start building with Nexios!

---

## 📂 Project Structure

```
project-name/
├── src/              # Your source code
│   └── project/     
├── tests/            # Test files
├── docs/             # Documentation (VitePress)
├── pyproject.toml    # Project metadata & dependencies
└── README.md
```

If you don’t want to use the `src` folder, feel free to rename it and update imports.

---

## 📦 Releasing

1. Update the version in `pyproject.toml` (follow [SemVer](https://semver.org/)).
2. Commit changes and push to `main`.
3. Create a GitHub release with the version tag (e.g. `v1.2.3`).
4. Publish!

---

Built with ❤️ by [@nexios-labs](https://github.com/nexios-labs)

