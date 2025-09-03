CREATE TABLE `events_table` (
	`id` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`timestamp` text DEFAULT (CURRENT_TIMESTAMP),
	`userId` text NOT NULL,
	`type` text NOT NULL,
	`meta` text
);
--> statement-breakpoint
CREATE TABLE `users_table` (
	`id` text PRIMARY KEY NOT NULL
);
