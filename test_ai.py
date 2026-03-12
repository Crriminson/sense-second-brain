# test_ai.py
"""
Run this to test AI module independently.
No database, no server, no nothing. Just AI.
"""

import asyncio
from ai import intents, answers, relations


async def test_intents():
    print("=" * 50)
    print("TESTING INTENT CLASSIFICATION")
    print("=" * 50)

    test_cases = [
        "Remember to fix the auth bug tomorrow",
        "What did I decide about the database?",
        "Switch to the hackathon project",
        "Open VS Code",
        "Open VS Code and play some music",
        "Start a meeting",
        "End the meeting",
        "What workspaces do I have?",
        "Toggle dark mode",
        "Enable focus mode",
        "Take a screenshot",
        "alksjdflkajsdf garbage input",
    ]

    for text in test_cases:
        print(f"\nInput: \"{text}\"")
        result = await intents.classify(text, active_workspace="General")
        print(f"  Intent:     {result['intent']} (confidence: {result['confidence']})")
        print(f"  Tags:       {result['tags']}")
        print(f"  Spoken:     {result['spoken_response']}")
        if result['pc_actions']:
            print(f"  PC Actions: {result['pc_actions']}")
        print()


async def test_answers():
    print("=" * 50)
    print("TESTING QUESTION ANSWERING")
    print("=" * 50)

    # Simulate notes from vector search
    fake_notes = [
        {"text": "Use PostgreSQL for the user database", "workspace": "Backend", "similarity": 0.87},
        {"text": "Actually switch to MongoDB instead of Postgres", "workspace": "Backend", "similarity": 0.85},
        {"text": "Database needs to handle 10k concurrent users", "workspace": "Backend", "similarity": 0.62},
    ]

    fake_edges = [
        {
            "rel_type": "contradicts",
            "source_text": "Use PostgreSQL for the user database",
            "target_text": "Actually switch to MongoDB instead of Postgres",
        }
    ]

    question = "What did I decide about the database?"
    print(f"\nQuestion: \"{question}\"")
    print(f"Notes provided: {len(fake_notes)}")
    print(f"Edges provided: {len(fake_edges)}")

    answer = await answers.answer(question, fake_notes, fake_edges)
    print(f"\nAnswer: {answer}")


async def test_relations():
    print("\n" + "=" * 50)
    print("TESTING RELATIONSHIP CLASSIFICATION")
    print("=" * 50)

    pairs = [
        ("Use PostgreSQL for the database", "Switch to MongoDB instead"),
        ("Use PostgreSQL for the database", "Set max_connections to 200 in PostgreSQL config"),
        ("Use PostgreSQL for the database", "The login page needs a redesign"),
    ]

    for a, b in pairs:
        print(f"\nNote A: \"{a}\"")
        print(f"Note B: \"{b}\"")
        result = await relations.classify(a, b)
        print(f"  Type:        {result['rel_type']}")
        print(f"  Weight:      {result['weight']}")
        print(f"  Explanation: {result['explanation']}")


async def test_summarize():
    print("\n" + "=" * 50)
    print("TESTING MEETING SUMMARIZATION")
    print("=" * 50)

    transcript = """
    Ok so I think we should use PostgreSQL for the main database.
    The schema should be normalized, at least for the user tables.
    John, can you set up the database server by Friday?
    We also need to figure out the auth system. Let's go with JWT tokens.
    Sarah mentioned she can handle the frontend auth flow.
    One more thing — we need to write migration scripts before the demo.
    """

    print(f"\nTranscript: {transcript[:100]}...")
    result = await answers.summarize(transcript)
    print(f"\nSummary: {result['summary']}")
    print(f"Action items:")
    for item in result['action_items']:
        print(f"  - {item}")


async def main():
    await test_intents()
    await test_answers()
    await test_relations()
    await test_summarize()


if __name__ == "__main__":
    asyncio.run(main())
