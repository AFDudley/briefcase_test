# AI Context Management Strategy

## Overview

This document provides guidance on managing AI context effectively during the refactoring project. Due to the limitations of AI context windows and memory, specific strategies should be used to ensure accurate and focused assistance.

## The Problem

Long conversations with AI assistants face several challenges:
- **Context window limits** - Earlier parts of conversations get truncated
- **Information overload** - Too much context can lead to confused or mixed responses  
- **Drift** - The AI may lose focus on the current task
- **Inconsistency** - Details from different phases may get conflated

## Recommended Strategy: Fresh Context Per Phase

### Starting a New Phase

For each refactoring phase or major task, start a fresh conversation with this template:

```
I'm working on refactoring [specific module] following the standards in 01_CODING_STANDARDS.md.

Current task: [Phase X.Y - Specific description]
Files involved: [List only relevant files]

Here's the current code:
[Paste only the relevant sections]

Specific goal: [What should be accomplished]
```

### Example Context Setting

```
I'm working on refactoring ssh_utils.py following the standards in 01_CODING_STANDARDS.md.

Current task: Phase 1.1 - Extract SSH key loading into reusable function
Files involved: ssh_utils.py, app.py

Here's the current code:
[Current test_ssh_connection function]
[Current generate_ed25519_key function]

Specific goal: Extract common key loading logic into a load_ssh_key() function that handles multiple key types with proper error propagation.
```

## What to Include in Context

### Always Include:
1. **Current phase** from 03_REFACTORING_PHASES.md
2. **Relevant code sections** (not entire files)
3. **Specific goal** for this conversation
4. **Key standards** that apply to this task

### Never Include:
1. **Unrelated modules** or phases
2. **Historical discussion** from previous phases
3. **Completed work** unless directly relevant
4. **Entire file contents** when only specific functions matter

## Templates for Common Scenarios

### Code Review Request
```
Please review this refactored code against 01_CODING_STANDARDS.md:

Original function: [paste original]
Refactored version: [paste new version]

Check specifically for:
- Function length (<50 lines)
- Pure functions where possible
- Proper error propagation
- Type hints
```

### Testing Request
```
I need to test this refactored function using ios-interact:

Function: [paste function]
Test approach from 04_TESTING_STRATEGY.md: [relevant section]

Please provide the ios-interact commands to test this functionality.
```

### Implementation Request
```
Implement Phase X.Y from 03_REFACTORING_PHASES.md:

Current code:
[paste current implementation]

Requirements:
- [Specific requirements from phase doc]
- Follow fail-fast principle
- Use type hints
- Keep functions under 50 lines
```

## Managing Long Refactoring Sessions

If you must continue a long conversation:

### Periodic Summaries
Every 5-10 exchanges, request:
```
"Please summarize:
1. What we've completed
2. Current task status  
3. Next steps"
```

### Explicit Focus
Be very specific about what to focus on:
```
"For the next responses, only consider:
- The load_ssh_key() function
- Its usage in test_ssh_connection()
- No other refactoring tasks"
```

### Context Pruning
Explicitly state what to ignore:
```
"We've completed Phase 1.1. You can ignore:
- Previous discussion about button configs
- Deleted test files
- Any ansible-related refactoring"
```

## Red Flags Requiring Fresh Context

Start a new conversation if you notice:
- AI referencing deleted files or old code
- Mixing requirements from different phases
- Confusion about the current task
- Inconsistent application of standards
- References to discussions from much earlier

## Documentation Between Sessions

After each phase, document:
1. What was completed
2. Any deviations from the plan
3. Unexpected issues found
4. Testing results

This helps set context for the next session without requiring full conversation history.

## Quick Context Check

Before each major code change, verify the AI understands:
```
"Before we proceed, confirm you understand:
1. Current task: [what]
2. Files to modify: [which]
3. Key standards: [what rules apply]"
```

## Best Practices

1. **One phase per conversation** when possible
2. **Paste specific code** not entire files
3. **Reference documents** by name, not full content
4. **Be explicit** about what to ignore
5. **Start fresh** if confusion arises

Remember: A focused AI with clear context produces better results than one trying to juggle too much information.