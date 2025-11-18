"""Main entry point for the Web Automation Agent."""

import os
import sys
from src.agent.graph import run_agent
from src.utils.web_driver import sanitize_filename


def main():
    """
    Main function to run the web automation agent.
    """
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set")
        print("\nPlease set your API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        return 1

    # Print banner
    print("=" * 60)
    print("        Web Automation Agent")
    print("        Powered by LangGraph + Anthropic Claude")
    print("=" * 60)

    # Get user input
    print("\nPlease provide the following information:")
    url = input("Enter target URL: ").strip()
    query = input("Enter query: ").strip()

    # Validate input
    if not url or not query:
        print("\nError: URL and query are required")
        return 1

    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        print("\nError: URL must start with http:// or https://")
        return 1

    # Display task information
    print("\n" + "=" * 60)
    print(f"🚀 Starting agent for: {query}")
    print(f"🌐 Target: {url}")
    print("=" * 60 + "\n")

    # Run the agent
    try:
        print("⏳ Initializing agent...")
        result = run_agent(url, query)

        # Display results
        print("\n" + "=" * 60)
        print("✅ Agent completed successfully!")
        print("=" * 60)

        # Generate output filename
        filename = sanitize_filename(query)
        output_path = f"outputs/{filename}.md"

        print(f"\n📄 Output saved to: {output_path}")
        print(f"📊 Total steps: {len(result['plan_steps'])}")

        # Display step statuses
        if result['plan_steps']:
            success_count = sum(1 for step in result['plan_steps'] if step.status == "success")
            failed_count = sum(1 for step in result['plan_steps'] if step.status == "failed")
            print(f"   ✓ Successful: {success_count}")
            print(f"   ✗ Failed: {failed_count}")

        print(f"📝 Guide items: {len(result['guide_items'])}")

        # Display errors if any
        if result['error_log']:
            print(f"\n⚠️  Errors encountered: {len(result['error_log'])}")
            print("\nError details:")
            for idx, error in enumerate(result['error_log'], 1):
                print(f"  {idx}. {error}")

        # Display guide categories
        if result['guide_items']:
            categories = {}
            for item in result['guide_items']:
                categories[item.category] = categories.get(item.category, 0) + 1

            print(f"\n📚 Guide breakdown:")
            for category, count in categories.items():
                category_name = category.replace('_', ' ').title()
                print(f"   • {category_name}: {count}")

        print("\n" + "=" * 60)
        print("🎉 Done! Check the output file for full details.")
        print("=" * 60 + "\n")

        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Agent interrupted by user")
        return 130

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ Error occurred:")
        print("=" * 60)
        print(f"\n{str(e)}\n")

        # Print traceback for debugging
        import traceback
        print("Traceback:")
        traceback.print_exc()

        return 1


if __name__ == "__main__":
    sys.exit(main())
