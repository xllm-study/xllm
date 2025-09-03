if (!process.env.DB_FILE_NAME) {
  const default_db_file = "file:local.db";
  console.warn(
    "DB_FILE_NAME environment variable is not set, defaulting to " +
      default_db_file,
  );
  process.env.DB_FILE_NAME = default_db_file;
}

if (!process.env.PORT) {
  const default_port = "5174";
  console.warn(
    "PORT environment variable is not set, defaulting to " + default_port,
  );
  process.env.PORT = default_port;
}

if (!process.env.DATA_PATH) {
  const default_data_path =
    "/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/data/web/";
  console.warn(
    "DATA_PATH environment variable is not set, defaulting to " +
      default_data_path,
  );
  process.env.DATA_PATH = default_data_path;
}

if (!process.env.EXPORT_PATH) {
  const default_export_path =
    "/sc/arion/projects/hpims-hpi/user/janssm02/data_extraction_w_LLM/web/export";
  console.warn(
    "EXPORT_PATH environment variable is not set, defaulting to " +
      default_export_path,
  );
  process.env.EXPORT_PATH = default_export_path;
}

if (!process.env.migrations_folder) {
  const default_migrations_folder = "drizzle";
  console.warn(
    "MIGRATIONS_FOLDER environment variable is not set, defaulting to " +
      default_migrations_folder,
  );
  process.env.migrations_folder = default_migrations_folder;
}

export const CONFIG = {
  DB_FILE_NAME: process.env.DB_FILE_NAME,
  PORT: parseInt(process.env.PORT, 10),
  DATA_PATH: process.env.DATA_PATH,
  EXPORT_PATH: process.env.EXPORT_PATH,
  MIGRATIONS_FOLDER: process.env.migrations_folder,
} as const;
