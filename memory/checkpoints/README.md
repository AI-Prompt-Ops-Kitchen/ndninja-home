# Checkpoints — Named Save Points

This directory stores named checkpoints created during conversations.
Each checkpoint captures the working context at a specific moment.

## Format
`YYYY-MM-DD_HH-MM_checkpoint-name.md`

## Restore
To restore from a checkpoint, read the file and load its context.

## Auto-Cleanup
Checkpoints older than 7 days may be archived to `checkpoints/archive/`
