#!/usr/bin/env python3
"""
CUGAr-SALES Interactive Demo

Simple interactive version for live demonstrations.
Shows capability-first architecture with human-in-the-loop guardrails.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from cuga.modular.tools.sales.outreach import draft_outbound_message
from datetime import datetime


def print_header():
    """Print demo header."""
    print("\n" + "=" * 80)
    print("🎯 CUGAr-SALES: Capability-First Sales Automation Demo")
    print("=" * 80)
    print("\nKey Principles:")
    print("  ✓ Capability-first (not vendor-locked)")
    print("  ✓ Human-in-the-loop (never auto-sends)")
    print("  ✓ Offline-capable (no external APIs)")
    print("  ✓ Explainable (full traceability)")
    print("=" * 80 + "\n")


def get_user_input() -> dict:
    """Get prospect information from user."""
    print("📝 Enter prospect information:\n")
    
    first_name = input("First Name: ").strip() or "Jane"
    company = input("Company: ").strip() or "Acme Corp"
    product = input("Product/Service: ").strip() or "Enterprise Platform"
    industry = input("Industry: ").strip() or "Technology"
    use_case = input("Use Case: ").strip() or "customer analytics"
    
    return {
        "first_name": first_name,
        "company": company,
        "product": product,
        "industry": industry,
        "use_case": use_case,
    }


def select_template() -> str:
    """Let user select or create a template."""
    print("\n📋 Select message template:\n")
    
    templates = {
        "1": {
            "name": "Renewal Follow-up",
            "template": """Subject: Quick question about {{company}}'s renewal

Hi {{first_name}},

I wanted to reach out regarding {{company}}'s upcoming renewal for {{product}}.

We've seen great results with {{industry}} companies like yours, and I'd love to explore how we can continue supporting your {{use_case}} goals in the next year.

Would you have 15 minutes next week to discuss?

Best regards,
Sarah Thompson""",
        },
        "2": {
            "name": "Introduction",
            "template": """Subject: Helping {{industry}} companies with {{use_case}}

Hi {{first_name}},

I came across {{company}} and was impressed by your work in {{industry}}.

We help companies like yours optimize {{use_case}} with {{product}}. I'd love to share some insights that might be relevant.

Are you available for a brief call next week?

Best,
Sarah Thompson""",
        },
        "3": {
            "name": "Custom",
            "template": None,
        },
    }
    
    for key, value in templates.items():
        print(f"  {key}. {value['name']}")
    
    choice = input("\nSelect (1-3): ").strip() or "1"
    
    if choice == "3":
        print("\nEnter your template (use {{variable_name}} for personalization):")
        print("(Press Ctrl+D or Ctrl+Z when done)\n")
        lines = []
        try:
            while True:
                line = input()
                lines.append(line)
        except EOFError:
            pass
        return "\n".join(lines)
    
    return templates.get(choice, templates["1"])["template"]


def run_demo():
    """Run interactive demo."""
    print_header()
    
    # Get inputs
    prospect_data = get_user_input()
    template = select_template()
    
    # Create execution context
    trace_id = f"demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    print("\n⚙️  Processing with capability: draft_outbound_message")
    print(f"    Trace ID: {trace_id}")
    print(f"    Profile: demo")
    print(f"    Domain: engagement")
    print("\n" + "-" * 80)
    
    # Execute capability
    inputs = {
        "template": template,
        "prospect_data": prospect_data,
        "channel": "email",
        "tone": "professional",
    }
    
    context = {
        "trace_id": trace_id,
        "profile": "demo",
    }
    
    result = draft_outbound_message(inputs, context)
    
    # Present result
    print("\n" + "=" * 80)
    print("✅ DRAFT MESSAGE READY FOR REVIEW")
    print("=" * 80)
    print(f"\n📧 SUBJECT: {result['subject']}")
    print("-" * 80)
    print(result['message_draft'])
    print("-" * 80)
    
    # Show metadata
    print("\n📊 ANALYSIS:")
    print(f"  • Status: {result['status']} (REQUIRES HUMAN APPROVAL)")
    print(f"  • Personalization: {result['metadata']['personalization_score']:.0%}")
    print(f"  • Word Count: {result['metadata']['word_count']}")
    print(f"  • Variables Used: {', '.join(result['variables_used'])}")
    
    if result['missing_variables']:
        print(f"  ⚠️  Missing Variables: {', '.join(result['missing_variables'])}")
    
    # Show guardrails
    print("\n🛡️ GUARDRAILS ENFORCED:")
    print("  ✓ Status is 'draft' (never 'sent')")
    print("  ✓ Human approval required before sending")
    print("  ✓ Offline execution (no external API calls)")
    print("  ✓ Full traceability with trace_id")
    print("  ✓ Capability-first (not vendor-specific)")
    
    # Next steps
    print("\n" + "=" * 80)
    print("📋 NEXT STEPS:")
    print("  1. Review the draft message above")
    print("  2. Make any necessary edits")
    print("  3. Manually send via your preferred tool")
    print("  4. System will NEVER auto-send")
    print("=" * 80 + "\n")
    
    # Offer to continue
    another = input("Create another draft? (y/n): ").strip().lower()
    if another == "y":
        run_demo()


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        print("\n\n👋 Demo terminated. Thank you!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
