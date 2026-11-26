#!/usr/bin/env python3
"""Validate the lesson drafts before they are allowed to be published.

Checks status, forbidden markers, quiz count, scenes and scene geometry.
"""

from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LESSONS = os.path.join(ROOT, "lessons")


def main() -> int:
    rows = []
    problems = []

    for lesson_json in sorted(glob.glob(os.path.join(LESSONS, "*", "lesson.json"))):
        folder = os.path.dirname(lesson_json)
        name = os.path.basename(folder)
        meta = json.load(open(lesson_json, encoding="utf-8"))
        body_path = os.path.join(folder, "body.md")
        body = open(body_path, encoding="utf-8").read() if os.path.exists(body_path) else ""
        quiz_path = os.path.join(folder, "quiz.json")
        quiz = json.load(open(quiz_path, encoding="utf-8")) if os.path.exists(quiz_path) else []
        scenes = sorted(glob.glob(os.path.join(folder, "scenes", "*.json")))

        chapters = body.count("\n## ")
        rows.append((name, meta.get("status"), chapters, len(scenes), len(quiz)))

        if meta.get("status") != "final":
            problems.append("%s: status is %r" % (name, meta.get("status")))
        if any(word in body.lower() for word in ("draft", "todo")):
            problems.append("%s: body contains DRAFT/TODO" % name)
        min_quiz = 0 if name.startswith("00") else 8
        if len(quiz) < min_quiz:
            problems.append("%s: only %d quiz questions" % (name, len(quiz)))
        if not scenes:
            problems.append("%s: no scenes" % name)
        for question in quiz:
            if not isinstance(question.get("options"), list) or len(question["options"]) != 4:
                problems.append("%s: quiz options must have 4 entries" % name)
            if not isinstance(question.get("answer"), int) or not 0 <= question["answer"] < 4:
                problems.append("%s: quiz answer index out of range" % name)

        for scene_path in scenes:
            try:
                scene = json.load(open(scene_path, encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                problems.append("%s: invalid JSON %s (%s)" % (name, scene_path, exc))
                continue
            width = scene.get("width", 0)
            height = scene.get("height", 0)
            if not scene.get("steps"):
                problems.append("%s: %s has no steps" % (name, os.path.basename(scene_path)))
            for step in scene.get("steps", []):
                if not step.get("caption"):
                    problems.append("%s: %s step without caption" % (name, os.path.basename(scene_path)))
                ids = set()
                for obj in step.get("objects", []):
                    oid = obj.get("id")
                    if not oid:
                        problems.append("%s: object without id" % name)
                    elif oid in ids:
                        problems.append("%s: duplicate object id %s" % (name, oid))
                    ids.add(oid)
                    if "type" not in obj:
                        problems.append("%s: object %s without type" % (name, oid))
                    for key in ("x", "x1", "x2"):
                        if key in obj and not (0 <= obj[key] <= width + 10):
                            problems.append("%s: %s.%s outside canvas" % (name, oid, key))
                    for key in ("y", "y1", "y2"):
                        if key in obj and not (0 <= obj[key] <= height + 10):
                            problems.append("%s: %s.%s outside canvas" % (name, oid, key))

    print("%-22s %-7s %8s %6s %5s" % ("Lektion", "Status", "Kapitel", "Szenen", "Quiz"))
    for name, status, chapters, scenes, quiz in rows:
        print("%-22s %-7s %8d %6d %5d" % (name, status, chapters, scenes, quiz))
    print()
    if problems:
        for problem in problems:
            print("FAIL  " + problem)
        print("\n%d Problem(e)." % len(problems))
        return 1
    print("LESSON-CHECK BESTANDEN — %d Lektion(en)." % len(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
