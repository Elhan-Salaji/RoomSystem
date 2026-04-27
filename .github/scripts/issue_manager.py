#!/usr/bin/env python3
"""
AI Issue Manager for RoomSystem.
Triggered on issues:opened — improves description, sets labels/milestone,
splits into sub-issues, sets relationships, adds to GitHub Project.
"""

import json
import os
import re
import sys
import time
from typing import Any

import requests
from anthropic import Anthropic

# ── Config ────────────────────────────────────────────────────────────────────

REPO = os.environ["GITHUB_REPOSITORY"]
OWNER, REPO_NAME = REPO.split("/", 1)
ISSUE_NUMBER = int(os.environ["ISSUE_NUMBER"])
ISSUE_TITLE = os.environ.get("ISSUE_TITLE", "")
ISSUE_BODY = os.environ.get("ISSUE_BODY", "")
ISSUE_NODE_ID = os.environ.get("ISSUE_NODE_ID", "")
GH_TOKEN = os.environ["GITHUB_TOKEN"]
GH_PAT = os.environ.get("GH_PAT") or GH_TOKEN  # PAT with project scope for Projects v2
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
GH_PROJECT_HEADERS = {
    "Authorization": f"Bearer {GH_PAT}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
GH_BASE = "https://api.github.com"

claude = Anthropic(api_key=ANTHROPIC_KEY)

# ── GitHub REST helpers ───────────────────────────────────────────────────────

def gh_get(path: str, params: dict | None = None) -> Any:
    r = requests.get(f"{GH_BASE}{path}", headers=GH_HEADERS, params=params)
    r.raise_for_status()
    return r.json()


def gh_patch(path: str, data: dict) -> Any:
    r = requests.patch(f"{GH_BASE}{path}", headers=GH_HEADERS, json=data)
    r.raise_for_status()
    return r.json()


def gh_post(path: str, data: dict) -> Any:
    r = requests.post(f"{GH_BASE}{path}", headers=GH_HEADERS, json=data)
    r.raise_for_status()
    return r.json()


def graphql(query: str, variables: dict | None = None) -> dict:
    r = requests.post(
        "https://api.github.com/graphql",
        headers={**GH_PROJECT_HEADERS, "Accept": "application/json"},
        json={"query": query, "variables": variables or {}},
    )
    r.raise_for_status()
    data = r.json()
    if "errors" in data:
        print(f"GraphQL warning: {data['errors']}", file=sys.stderr)
    return data.get("data", {})

# ── Data fetching ─────────────────────────────────────────────────────────────

def get_issues_summary() -> list[dict]:
    issues, page = [], 1
    while len(issues) < 50:
        batch = gh_get(
            f"/repos/{REPO}/issues",
            {"state": "open", "per_page": 30, "page": page},
        )
        if not batch:
            break
        for i in batch:
            if i["number"] != ISSUE_NUMBER and i.get("pull_request") is None:
                issues.append({
                    "number": i["number"],
                    "title": i["title"],
                    "labels": [l["name"] for l in i.get("labels", [])],
                    "milestone": i["milestone"]["title"] if i.get("milestone") else None,
                })
        page += 1
        if len(batch) < 30:
            break
    return issues


def get_milestones() -> list[dict]:
    ms = gh_get(f"/repos/{REPO}/milestones", {"state": "open", "per_page": 50})
    return [
        {
            "number": m["number"],
            "title": m["title"],
            "description": (m.get("description") or "")[:120],
        }
        for m in ms
    ]


def get_labels() -> list[str]:
    labels = gh_get(f"/repos/{REPO}/labels", {"per_page": 100})
    return [l["name"] for l in labels]


def get_repo_tree() -> list[str]:
    try:
        tree = gh_get(f"/repos/{REPO}/git/trees/develop", {"recursive": "1"})
        return [
            item["path"]
            for item in tree.get("tree", [])
            if item["type"] == "blob" and item["path"].endswith(".java")
        ][:50]
    except Exception:
        return []

# ── Claude analysis ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an AI assistant managing GitHub issues for RoomSystem — a Spring Boot backend + Raspberry Pi mmWave room occupancy detection system.

Backend: Java 21, Spring Boot 4.x, InfluxDB 3.x, Package by Feature (com.roomsystem.feature.<name>), TDD (JUnit 5 + Mockito).
Features: database, receiver, authentication, forecast, provider.
Pi side: Python, DBSCAN clustering, STOMP/REST to backend.

Issue format to follow:
# Title
## Context
## Purpose / What Needs to Be Done
## Acceptance Criteria (checkboxes)
## Notes (optional)

An issue is TOO LARGE if it has 3+ unrelated technical concerns or is difficulty::high with multiple distinct implementation areas.

Respond ONLY with valid JSON — no markdown fences, no extra text."""


def analyze_with_claude(
    labels: list[str],
    milestones: list[dict],
    issues_summary: list[dict],
    tree: list[str],
) -> dict:
    prompt = f"""Analyze this new GitHub issue and return a JSON response.

TITLE: {ISSUE_TITLE}
BODY:
{ISSUE_BODY or "(empty)"}

AVAILABLE LABELS: {json.dumps(labels)}

AVAILABLE MILESTONES:
{json.dumps(milestones, indent=2)}

EXISTING ISSUES (for context and relationships):
{json.dumps(issues_summary[:40], indent=2)}

REPO JAVA FILES:
{chr(10).join(tree)}

Return this exact JSON structure:
{{
  "improved_title": "concise technical title",
  "improved_body": "full markdown body following the issue format",
  "labels": ["label1", "label2"],
  "milestone_number": <number or null>,
  "needs_split": <true or false>,
  "sub_issues": [
    {{
      "title": "string",
      "body": "full markdown body",
      "labels": ["label1", "subissue"],
      "milestone_number": <number or null>
    }}
  ],
  "related_issue_numbers": [<max 3 issue numbers>],
  "project_status": "Todo"
}}

Rules:
- Only use labels from AVAILABLE LABELS. Always include difficulty::*, priority::*, and component label (backend/raspberry pi).
- Always add "subissue" label to every sub_issue entry.
- Only use milestone numbers from AVAILABLE MILESTONES.
- sub_issues must be [] when needs_split is false.
- If the body is already detailed and well-structured, improve minimally.
- related_issue_numbers: only truly related issues, max 3."""

    response = claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    raw = re.sub(r"^```json\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)

# ── GitHub Projects v2 ────────────────────────────────────────────────────────

def find_project() -> tuple[str | None, str | None, str | None]:
    """Returns (projectId, statusFieldId, todoOptionId) or (None, None, None)."""
    try:
        data = graphql(
            """
            query($owner: String!, $name: String!) {
              repository(owner: $owner, name: $name) {
                projectsV2(first: 10) {
                  nodes {
                    id
                    title
                    fields(first: 20) {
                      nodes {
                        ... on ProjectV2SingleSelectField {
                          id
                          name
                          options { id name }
                        }
                      }
                    }
                  }
                }
              }
            }
            """,
            {"owner": OWNER, "name": REPO_NAME},
        )
        projects = data.get("repository", {}).get("projectsV2", {}).get("nodes", [])
        for project in projects:
            if "roomsystem" in project["title"].lower():
                project_id = project["id"]
                for field in project.get("fields", {}).get("nodes", []):
                    if not field or "name" not in field:
                        continue
                    if field["name"].lower() in ("status", "spalte", "column", "state"):
                        field_id = field["id"]
                        for opt in field.get("options", []):
                            if opt["name"].lower() in ("todo", "to do", "backlog"):
                                return project_id, field_id, opt["id"]
                        if field.get("options"):
                            return project_id, field_id, field["options"][0]["id"]
                return project_id, None, None
    except Exception as e:
        print(f"Warning: Could not find project: {e}", file=sys.stderr)
    return None, None, None


def add_to_project(
    node_id: str,
    project_id: str,
    field_id: str | None,
    option_id: str | None,
) -> None:
    data = graphql(
        """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """,
        {"projectId": project_id, "contentId": node_id},
    )
    item_id = data.get("addProjectV2ItemById", {}).get("item", {}).get("id")
    if item_id and field_id and option_id:
        graphql(
            """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: String!) {
              updateProjectV2ItemFieldValue(input: {
                projectId: $projectId
                itemId: $itemId
                fieldId: $fieldId
                value: { singleSelectOptionId: $optionId }
              }) {
                projectV2Item { id }
              }
            }
            """,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "optionId": option_id,
            },
        )

# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print(f"Processing issue #{ISSUE_NUMBER}: {ISSUE_TITLE}")

    # 1. Gather context in parallel-ish (sequential for simplicity)
    print("Fetching repo context...")
    labels = get_labels()
    milestones = get_milestones()
    issues_summary = get_issues_summary()
    tree = get_repo_tree()

    # 2. Analyze with Claude
    print("Analyzing with Claude Sonnet 4.6...")
    try:
        result = analyze_with_claude(labels, milestones, issues_summary, tree)
    except Exception as e:
        print(f"Claude analysis failed: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"  split={result.get('needs_split')} | "
        f"labels={result.get('labels')} | "
        f"milestone={result.get('milestone_number')}"
    )

    # 3. Update original issue
    update_payload: dict[str, Any] = {
        "title": result["improved_title"],
        "body": result["improved_body"],
        "labels": result.get("labels", []),
    }
    if result.get("milestone_number"):
        update_payload["milestone"] = result["milestone_number"]

    gh_patch(f"/repos/{REPO}/issues/{ISSUE_NUMBER}", update_payload)
    print(f"✓ Issue #{ISSUE_NUMBER} updated")

    # 4. Add related issues section if not already referenced
    related = [n for n in result.get("related_issue_numbers", []) if isinstance(n, int)]
    if related:
        current_body = result["improved_body"]
        if not any(f"#{n}" in current_body for n in related):
            related_md = "\n\n## Related Issues\n" + "\n".join(f"- #{n}" for n in related)
            gh_patch(
                f"/repos/{REPO}/issues/{ISSUE_NUMBER}",
                {"body": current_body + related_md},
            )
            print(f"✓ Related issues added: {related}")

    # 5. Find GitHub Project
    project_id, field_id, option_id = find_project()

    # 6. Add original issue to project
    if project_id and ISSUE_NODE_ID:
        try:
            add_to_project(ISSUE_NODE_ID, project_id, field_id, option_id)
            print(f"✓ Issue #{ISSUE_NUMBER} added to GitHub Project")
        except Exception as e:
            print(f"Warning: Could not add to project: {e}", file=sys.stderr)

    # 7. Create sub-issues
    if result.get("needs_split") and result.get("sub_issues"):
        sub_issues = result["sub_issues"]
        print(f"Splitting into {len(sub_issues)} sub-issues...")

        for sub in sub_issues:
            sub_payload: dict[str, Any] = {
                "title": sub["title"],
                "body": sub["body"],
                "labels": sub.get("labels", []),
            }
            if sub.get("milestone_number"):
                sub_payload["milestone"] = sub["milestone_number"]

            created = gh_post(f"/repos/{REPO}/issues", sub_payload)
            sub_number = created["number"]
            sub_node_id = created.get("node_id", "")
            sub_db_id = created["id"]

            print(f"  ✓ Created sub-issue #{sub_number}: {sub['title']}")

            # Link as sub-issue
            try:
                gh_post(
                    f"/repos/{REPO}/issues/{ISSUE_NUMBER}/sub_issues",
                    {"sub_issue_id": sub_db_id},
                )
                print(f"    ✓ Linked #{sub_number} → #{ISSUE_NUMBER}")
            except Exception as e:
                print(f"    Warning: Sub-issue link failed: {e}", file=sys.stderr)

            # Add sub-issue to project
            if project_id and sub_node_id:
                try:
                    add_to_project(sub_node_id, project_id, field_id, option_id)
                except Exception as e:
                    print(f"    Warning: Project add failed: {e}", file=sys.stderr)

            time.sleep(0.5)

    print(f"\n✓ Done — issue #{ISSUE_NUMBER} fully processed.")


if __name__ == "__main__":
    main()
