import argparse
import database
from registry import AIRegistry
from ai import flux, gemini, llama, midjourney, whisper


def main():
    parser = argparse.ArgumentParser(
        description="Initialize AI Models table and ensure Users table exists.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--initial-rating",
        type=int,
        default=1000,
        help="Initial rating for newly added AI models."
    )
    parser.add_argument(
        "--force-reset-models",
        action="store_true",
        help="!!! DANGER !!! Drop the existing ai_models table and ratings before initializing."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output (e.g., show skipped models)."
    )

    args = parser.parse_args()

    db_file_display_name = database.DATABASE_FILE

    print(f"Using database file: {db_file_display_name}")

    if args.force_reset_models:
        print("\n--- WARNING: --force-reset-models flag detected ---")
        confirm = input(
            f"This will DELETE the 'ai_models' table and all model ratings in '{db_file_display_name}'. Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            print("Proceeding with AI models table reset...")
            database.drop_ai_models_table()
            print(f"Table 'ai_models' dropped.")
        else:
            print("Aborted due to lack of confirmation.")
            return

    print("\nInitializing database tables (if needed)...")
    database.initialize_database()

    print("Loading models from registry...")
    registry = AIRegistry()
    all_models = registry.get_all_models()

    if not all_models:
        print("Warning: No models found in the registry. Ensure model modules are imported.")
    else:
        print(f"\nFound {len(all_models)} models in registry. Syncing with 'ai_models' table...")
        added_count = 0
        skipped_count = 0
        for model_instance in all_models:
            try:
                model_id = f"{model_instance.meta.provider.lower()}:{model_instance.meta.version}"
                display_name = f"{model_instance.meta.provider} {model_instance.meta.version}"

                added = database.add_model_if_not_exists(
                    model_id,
                    display_name,
                    initial_rating=args.initial_rating
                )
                if added:
                    added_count += 1
                else:
                    skipped_count += 1
                    if args.verbose:
                        print(f"Model already in DB, skipped: {model_id}")

            except AttributeError:
                print(f"Warning: Skipping an object that doesn't seem to be a registered model: {model_instance}")
            except Exception as e:
                print(f"Error processing model {getattr(model_instance, 'meta', 'UNKNOWN')}: {e}")

        print(f"\nAI Models sync finished. Added: {added_count}, Skipped: {skipped_count}")

    print("-" * 20)
    print("Current AI models in DB (Top 10 by rating):")
    models_in_db = database.get_models_sorted_by_rating(limit=10)
    if models_in_db:
        for mid, dname, rating in models_in_db:
            print(f"- {dname} ({mid}): Rating {rating}")
    else:
        print("No AI models found in the database.")

    print("-" * 20)
    print(f"Database initialization/sync complete for '{db_file_display_name}'.")


if __name__ == "__main__":
    main()
