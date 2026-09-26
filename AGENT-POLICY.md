# Agent Policy

The svcdesk agent uses a narrow denylist to reduce the blast radius of automated actions.

- Bash(rm *): Prevents the agent from deleting project files or directories and accidentally destroying repository content.
- Bash(git push *): Prevents the agent from publishing commits or tags to the remote repository without explicit human control.
- Bash(docker *): Prevents the agent from starting, stopping, deleting or otherwise changing Docker resources outside the intended workflow.
- WebFetch: Prevents the agent from retrieving arbitrary external content that is unnecessary for implementing the local laboratory specification.