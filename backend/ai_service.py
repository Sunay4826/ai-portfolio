import os
import re
from pathlib import Path
from typing import List

import httpx
from dotenv import load_dotenv

ENV_PATH = Path(__file__).with_name(".env")


def _settings() -> dict[str, str]:
    # Force .env values to override stale process env values.
    load_dotenv(ENV_PATH, override=True)
    return {
        "openrouter_api_key": os.getenv("OPENROUTER_API_KEY", "").strip(),
        "openrouter_model": os.getenv(
            "OPENROUTER_MODEL", "meta-llama/llama-3.3-8b-instruct:free"
        ).strip(),
        "gemini_api_key": os.getenv("GEMINI_API_KEY", "").strip(),
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
        "app_url": os.getenv("APP_URL", "http://localhost:5173").strip(),
        "site_name": os.getenv("SITE_NAME", "Portfolio AI").strip(),
    }


def _load_resume() -> str:
    resume_path = Path(__file__).with_name("resume.md")
    if not resume_path.exists():
        return "Resume data not available."
    return resume_path.read_text(encoding="utf-8")


def _chunk_text(text: str, chunk_size: int = 220) -> List[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunks.append(" ".join(words[i : i + chunk_size]))
    return chunks or [text]


def _simple_retrieve(question: str, resume_text: str, top_k: int = 2) -> str:
    chunks = _chunk_text(resume_text)
    question_terms = set(question.lower().split())

    scored = []
    for chunk in chunks:
        chunk_terms = set(chunk.lower().split())
        score = len(question_terms.intersection(chunk_terms))
        scored.append((score, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [chunk for _, chunk in scored[:top_k]]
    return "\n\n".join(selected)


def _is_technology_question(question: str) -> bool:
    q = question.lower()
    if "technology" in q or "technologies" in q or "tech stack" in q:
        return True
    if "strongest" in q and ("tech" in q or "technology" in q or "technologies" in q):
        return True
    # Keep this scoped to technical-skill intent, not soft-skill intent.
    triggers = [
        "technical skills",
        "frameworks",
        "languages",
        "tools",
        "frontend stack",
        "backend stack",
    ]
    return any(t in q for t in triggers)


def _is_backend_question(question: str) -> bool:
    q = question.lower()
    backend_terms = ["backend", "rest api", "api", "node.js", "express", "postgresql"]
    intent_terms = ["what kind", "experience", "work", "done", "built"]
    return any(b in q for b in backend_terms) and any(i in q for i in intent_terms)


def _is_project_question(question: str) -> bool:
    q = question.lower()
    return "project" in q and any(
        k in q for k in ["made", "build", "built", "created", "which", "what", "give", "name", "list"]
    )


def _is_github_question(question: str) -> bool:
    q = question.lower()
    has_github = "github" in q or "git hub" in q
    return has_github and any(k in q for k in ["url", "link", "profile", "id", "give"])


def _is_softskills_question(question: str) -> bool:
    q = question.lower()
    soft_terms = [
        "communication",
        "leadership",
        "soft skills",
        "team collaboration",
        "time management",
        "critical thinking",
        "adaptability",
    ]
    return any(term in q for term in soft_terms)


def _is_why_hire_question(question: str) -> bool:
    q = question.lower()
    return "why hire" in q or "why should we hire" in q


def _is_intro_question(question: str) -> bool:
    q = question.lower()
    triggers = ["tell me about yourself", "introduce yourself", "60 second intro", "self introduction"]
    return any(t in q for t in triggers)


def _is_projects_pitch_question(question: str) -> bool:
    q = question.lower()
    return ("projects" in q and "30" in q) or "projects in 30 sec" in q or "project pitch" in q


def _is_backend_strengths_question(question: str) -> bool:
    q = question.lower()
    return "backend strengths" in q or ("backend" in q and "strength" in q)


def _is_frontend_strengths_question(question: str) -> bool:
    q = question.lower()
    return "frontend strengths" in q or ("frontend" in q and "strength" in q)


def _is_age_question(question: str) -> bool:
    q = question.lower()
    return "age" in q or "how old" in q


def _is_contact_question(question: str) -> bool:
    q = question.lower()
    return any(k in q for k in ["contact", "email", "phone", "mobile", "linkedin", "linked in"])


def _is_skills_projects_question(question: str) -> bool:
    q = question.lower()
    has_skills = any(k in q for k in ["technical skills", "skills", "tech stack", "languages"])
    has_projects = any(k in q for k in ["major projects", "projects", "project name"])
    return has_skills and has_projects


def _extract_top_technologies(resume_text: str) -> List[tuple[str, int]]:
    tech_aliases = {
        "react": "React",
        "react.js": "React",
        "next.js": "Next.js",
        "node.js": "Node.js",
        "express.js": "Express.js",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "python": "Python",
        "sql": "SQL",
        "postgresql": "PostgreSQL",
        "mongodb": "MongoDB",
        "prisma": "Prisma",
        "tailwind": "Tailwind CSS",
        "tailwind css": "Tailwind CSS",
        "hono": "Hono",
        "cloudflare workers": "Cloudflare Workers",
        "vercel": "Vercel",
        "clerk": "Clerk",
        "socket.io": "Socket.IO",
        "langchain": "LangChain",
        "huggingface": "HuggingFace",
        "scikit-learn": "scikit-learn",
        "mysql": "MySQL",
        "git": "Git/GitHub",
        "github": "Git/GitHub",
    }
    text = resume_text.lower()
    scores: dict[str, int] = {}

    for raw, canonical in tech_aliases.items():
        pattern = r"\b" + re.escape(raw) + r"\b"
        count = len(re.findall(pattern, text))
        if count > 0:
            scores[canonical] = scores.get(canonical, 0) + count

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return ranked


def _build_technology_answer(resume_text: str) -> str:
    ranked = _extract_top_technologies(resume_text)
    if not ranked:
        return "I could not detect specific technologies from the current resume text."

    top = ranked[:8]
    names = [name for name, _ in top]
    top_line = ", ".join(names[:5])

    bullets = "\n".join([f"- {name}" for name in names])
    return (
        "Based on this resume, the strongest technologies are:\n"
        f"{bullets}\n\n"
        f"Most dominant stack signals: {top_line}."
    )


def _build_backend_answer(resume_text: str) -> str:
    lines = resume_text.splitlines()
    backend_points = []
    keywords = [
        "rest api",
        "node.js",
        "express",
        "postgresql",
        "prisma",
        "cloudflare workers",
        "authentication",
        "server-side",
        "database",
        "mysql",
        "socket.io",
    ]

    for line in lines:
        line_clean = line.strip("- ").strip()
        if not line_clean:
            continue
        low = line_clean.lower()
        if any(k in low for k in keywords):
            backend_points.append(line_clean)

    # Preserve order while deduplicating and keep concise.
    deduped = list(dict.fromkeys(backend_points))[:6]
    if not deduped:
        return "Backend work is not clearly listed in the current resume text."

    bullets = "\n".join([f"- {p}" for p in deduped])
    return f"Sunay's backend work includes:\n{bullets}"


def _build_projects_answer(resume_text: str) -> str:
    lines = [ln.strip() for ln in resume_text.splitlines()]
    project_titles = []
    project_links = []
    capture = False

    for line in lines:
        if line.lower().startswith("## major projects"):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if not capture:
            continue

        if line.startswith("### ") and ")" in line and " " in line:
            title = line.split(")", 1)[-1].strip()
            if title:
                project_titles.append(title)
        if "http://" in line or "https://" in line:
            project_links.append(line.lstrip("- ").strip())

    if not project_titles:
        return "Specific project names are not clearly listed in the current profile."

    bullets = "\n".join([f"- {name}" for name in project_titles])
    link_lines = "\n".join([f"- {ln}" for ln in project_links[:5]])
    return (
        "Projects Sunay has made:\n"
        f"{bullets}\n\n"
        "Available project links:\n"
        f"{link_lines if link_lines else '- No links listed.'}"
    )


def _build_github_answer(resume_text: str) -> str:
    urls = re.findall(r"https?://github\.com/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)?", resume_text)
    if not urls:
        return "GitHub URL is not listed in the current profile."

    unique = list(dict.fromkeys(urls))
    profile = None
    repos = []
    for u in unique:
        parts = u.rstrip("/").split("/")
        if len(parts) == 4 and profile is None:
            profile = u
        elif len(parts) >= 5:
            repos.append(u)

    if not profile and repos:
        # Infer profile from first repo path if direct profile is missing.
        parts = repos[0].rstrip("/").split("/")
        profile = "/".join(parts[:4])

    lines = []
    if profile:
        lines.append(f"GitHub profile: {profile}")
    if repos:
        lines.append("GitHub repositories:")
        lines.extend([f"- {r}" for r in repos[:5]])

    return "\n".join(lines)


def _extract_section(resume_text: str, section_name: str) -> str:
    lines = resume_text.splitlines()
    capture = False
    out: List[str] = []
    target = f"## {section_name}".lower()
    for line in lines:
        if line.strip().lower() == target:
            capture = True
            out.append(line)
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            out.append(line)
    return "\n".join(out).strip()


def _build_skills_projects_answer(resume_text: str) -> str:
    skills = _extract_section(resume_text, "Technical Skills")
    projects = _extract_section(resume_text, "Major Projects")
    if not skills and not projects:
        return "Technical skills and major projects are not clearly listed in the profile."
    parts = []
    if skills:
        parts.append(skills)
    if projects:
        parts.append(projects)
    return "\n\n".join(parts)


def _build_softskills_answer(resume_text: str) -> str:
    return (
        "Sunay's communication and leadership profile:\n"
        "- Communicates with honesty and clarity, especially when explaining real project work.\n"
        "- Shows leadership through ownership, consistency, and a builder mindset.\n"
        "- Works well independently and is open to feedback in collaborative settings.\n"
        "- Learns fast and keeps improving articulation with practice.\n"
        "- If a topic is new, he handles it with a growth mindset: he can learn it quickly and do better in the next iteration."
    )


def _build_why_hire_answer() -> str:
    return (
        "Why hire Sunay:\n"
        "- Strong combination of DSA discipline (C++) and real product execution.\n"
        "- Builds and deploys full-stack projects, not just local demos.\n"
        "- Works across frontend, backend, and AI-oriented product features.\n"
        "- Ownership mindset: learns fast, iterates quickly, and delivers end-to-end.\n"
        "- Startup-oriented thinking with focus on usable, scalable outcomes."
    )


def _build_intro_answer() -> str:
    return (
        "I’m Sunay Revad, a B.Tech ICT student at DA-IICT (2022-2026), based in Ahmedabad, Gujarat. "
        "I focus on building AI-driven full-stack products and I pair that with strong DSA practice in C++. "
        "My flagship project is AI Finance Platform, and I’ve also built a movie recommendation system, a full-stack blog platform, "
        "and an AI deterministic UI generator. I enjoy taking ideas from concept to deployed product, and I’m currently aiming for "
        "frontend/full-stack opportunities where I can contribute quickly and keep scaling my backend and AI skills."
    )


def _build_projects_pitch_answer() -> str:
    return (
        "Sunay’s projects in 30 seconds:\n"
        "- AI Finance Platform (flagship): AI-driven finance product with full-stack architecture.\n"
        "- Movie Recommendation System: personalized recommendations using similarity modeling.\n"
        "- Blog Platform: authentication-based content platform with dynamic publishing.\n"
        "- AI Deterministic UI Generator: schema-constrained UI generation pipeline with versioning and rollback.\n"
        "- Dataset Selection using ML: practical feature-selection and ML experimentation."
    )


def _build_backend_strengths_answer() -> str:
    return (
        "Sunay's backend strengths:\n"
        "- Node.js and Express.js fundamentals with RESTful API development.\n"
        "- Authentication flow design and integration.\n"
        "- Database work with MySQL and PostgreSQL.\n"
        "- Clean API integration mindset from full-stack project delivery.\n"
        "- Strong debugging and iterative improvement approach."
    )


def _build_frontend_strengths_answer() -> str:
    return (
        "Sunay's frontend strengths:\n"
        "- React.js and Next.js based product development.\n"
        "- Responsive UI implementation with clean component structure.\n"
        "- Tailwind CSS and shadcn/ui for fast, consistent interfaces.\n"
        "- Strong attention to usability, dashboard-style UX, and interaction clarity.\n"
        "- Experience shipping polished frontend on Vercel."
    )


def _build_age_answer(resume_text: str) -> str:
    match = re.search(r"Age:\s*([^\n]+)", resume_text, flags=re.IGNORECASE)
    if not match:
        return "Age is not listed in the profile."
    age_value = match.group(1).replace("(share only when asked)", "").strip()
    return f"Sunay is {age_value}."


def _build_contact_answer(resume_text: str) -> str:
    contact = _extract_section(resume_text, "Contact")
    if not contact:
        return "Contact details are not listed in the profile."
    return contact


async def answer_resume_question(question: str) -> tuple[str, str]:
    resume_text = _load_resume()
    context = _simple_retrieve(question, resume_text)
    settings = _settings()
    openrouter_api_key = settings["openrouter_api_key"]
    openrouter_model = settings["openrouter_model"]
    gemini_api_key = settings["gemini_api_key"]
    gemini_model = settings["gemini_model"]
    app_url = settings["app_url"]
    site_name = settings["site_name"]

    system_prompt = (
        "You are a portfolio assistant. Answer using only the provided resume context. "
        "If a detail is missing, say it is not listed in the resume. "
        "Keep responses concise, accurate, and professional. "
        "Use strengths-first language and frame improvement points positively (growth mindset), "
        "without negative or damaging phrasing. "
        "Never use the phrase 'beginner developer'."
    )

    user_prompt = (
        f"Resume context:\n{context}\n\n"
        f"User question: {question}\n\n"
        "Give a factual answer based only on context."
    )

    if _is_age_question(question):
        return (_build_age_answer(resume_text), "deterministic-age-parser")
    if _is_contact_question(question):
        return (_build_contact_answer(resume_text), "deterministic-contact-parser")
    if _is_why_hire_question(question):
        return (_build_why_hire_answer(), "deterministic-why-hire-parser")
    if _is_intro_question(question):
        return (_build_intro_answer(), "deterministic-intro-parser")
    if _is_projects_pitch_question(question):
        return (_build_projects_pitch_answer(), "deterministic-project-pitch-parser")
    if _is_backend_strengths_question(question):
        return (_build_backend_strengths_answer(), "deterministic-backend-strength-parser")
    if _is_frontend_strengths_question(question):
        return (_build_frontend_strengths_answer(), "deterministic-frontend-strength-parser")
    if _is_skills_projects_question(question):
        return (_build_skills_projects_answer(resume_text), "deterministic-skill-project-parser")
    if _is_softskills_question(question):
        return (_build_softskills_answer(resume_text), "deterministic-softskills-parser")
    if _is_technology_question(question):
        return (_build_technology_answer(resume_text), "deterministic-skill-parser")
    if _is_backend_question(question):
        return (_build_backend_answer(resume_text), "deterministic-backend-parser")
    if _is_project_question(question):
        return (_build_projects_answer(resume_text), "deterministic-project-parser")
    if _is_github_question(question):
        return (_build_github_answer(resume_text), "deterministic-github-parser")

    if openrouter_api_key and openrouter_api_key.startswith("sk-or-v1-"):
        headers = {
            "Authorization": f"Bearer {openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": app_url,
            "X-Title": site_name,
        }

        payload = {
            "model": openrouter_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 900,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 401:
                    return (
                    "OpenRouter returned 401 Unauthorized. Check OPENROUTER_API_KEY or use GEMINI_API_KEY.",
                        openrouter_model,
                    )
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            return (f"OpenRouter request failed: {exc}", openrouter_model)

        choices = data.get("choices", [])
        if not choices:
            return ("No response returned by model.", openrouter_model)

        message = choices[0].get("message", {})
        content = message.get("content", "No answer content.")
        return (content.strip(), openrouter_model)

    if gemini_api_key:
        gemini_model_candidates = [
            gemini_model,
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.5-flash-lite",
        ]
        # Preserve order and remove duplicates.
        gemini_model_candidates = list(dict.fromkeys(gemini_model_candidates))

        gemini_payload = {
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 900},
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            last_error = ""
            for candidate_model in gemini_model_candidates:
                gemini_url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/{candidate_model}:generateContent"
                )
                try:
                    response = await client.post(
                        gemini_url,
                        params={"key": gemini_api_key},
                        headers={"Content-Type": "application/json"},
                        json=gemini_payload,
                    )
                except httpx.HTTPError as exc:
                    last_error = f"Gemini request failed: {exc}"
                    continue

                if response.status_code == 401:
                    return (
                        "Gemini returned 401 Unauthorized. Verify GEMINI_API_KEY in backend/.env and restart backend.",
                        candidate_model,
                    )
                if response.status_code == 404:
                    last_error = (
                        f"Model '{candidate_model}' not found for Gemini API v1beta."
                    )
                    continue

                try:
                    response.raise_for_status()
                    data = response.json()
                except httpx.HTTPError as exc:
                    last_error = f"Gemini request failed: {exc}"
                    continue

                candidates = data.get("candidates", [])
                if not candidates:
                    last_error = f"No response returned by Gemini model '{candidate_model}'."
                    continue

                parts = candidates[0].get("content", {}).get("parts", [])
                text = " ".join([p.get("text", "") for p in parts]).strip()
                return (text or "No answer content.", candidate_model)

        return (
            f"Gemini request failed for all configured models. Last error: {last_error}",
            gemini_model,
        )

    return (
        "No valid model key found. Set OPENROUTER_API_KEY (sk-or-v1-...) or GEMINI_API_KEY in backend/.env.",
        "no-model",
    )
