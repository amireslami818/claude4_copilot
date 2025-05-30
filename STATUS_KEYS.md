# Football Match Status Keys

## Status ID Mapping

| Status ID | Description |
|-----------|-------------|
| 1 | Not started |
| 2 | First half |
| 3 | Half-time break |
| 4 | Second half |
| 5 | Extra time |
| 6 | Penalty shootout |
| 7 | Finished |
| 8 | Finished |
| 9 | Postponed |
| 10 | Canceled |
| 11 | To be announced |
| 12 | Interrupted |
| 13 | Abandoned |
| 14 | Suspended |

## Usage

These status IDs are used throughout the Football Bot pipeline to identify the current state of matches. The status is extracted in Step 2 and used for filtering and display purposes in subsequent steps.

**Note:** Status IDs 7 and 8 both map to "Finished" - this may indicate different types of finished states in the source API.
