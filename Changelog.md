# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] 2022-12-04
- Bot is marginally faster with better handling.
- Better structure, optimized a few aspects, code cleanup, no new features but some breaking changes!
#### Added
- refactor: Typehinted the entire library.
- refactor: Used `isort` and `black` for formatting.
- feat: Improved gateway message handling, added checks.
- feat: Added example config and usage files.
#### Changed
- feat!: Renamed `ws` to `gateway`.
- fix!: Changed structure of `ws_cache` in `DankCord.py`
- fix: Changed `_confirm_command_run` to use `ws_cache` as it should.
- fix!: Many typehints of IDs have been changed!
#### Removed
- feat!: Removed `_get_guild_id` as a class method, now internally resolved during gateway identify event.
- feat: Removed unnecessary imports, bloated code and unused methods.

## [Unreleased] - 2022-12-03
A new logger, improvements and new object.
#### Added
- feat: `Bot` object.
- feat: `Logger` class for DankCord.
#### Improved
- improve: Get the guild ID of the bot.

## [Unreleased] - 2022-12-02
A few major core additions and fixes.
#### Added
- feat: typehints to data in objects.
- feat: `Author` object.
- feat: `Embed` object.
- feat: `EmbedFooter` object.
- feat: `Emoji` object.
- feat: `DropdownComponent` object.
- feat: `DropdownOption` object.
- feat: `Button` object.
#### Fixed
- fix: Confirm if a slash command was sent or not.
