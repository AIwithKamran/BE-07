def calculate_cost(event_type: str, quantity: int, token_type: str = None) -> float:
    """
    Calculates the cost in cents for a given usage event.
    For AI tokens, costs vary by token category (input, output, thinking).
    """
    cost_in_cents = 0.0
    
    if event_type == "api_call":
        # Flat rate of $0.01 per API call (1 cent)
        cost_in_cents = quantity * 1.0

    elif event_type == "ai_tokens":
        if not token_type:
            # Default to input token cost if not specified
            token_type = "input"

        # Simulating different pricing tiers for different token types
        # (e.g. Gemini / OpenAI pricing models)
        if token_type == "input":
            # $0.0001 per input token (0.01 cents)
            cost_in_cents = quantity * 0.01
        elif token_type == "output":
            # $0.0004 per output token (0.04 cents)
            cost_in_cents = quantity * 0.04
        elif token_type == "thinking":
            # $0.0002 per thinking token (0.02 cents)
            cost_in_cents = quantity * 0.02
        else:
            raise ValueError(f"Unknown token type: {token_type}")

    else:
        raise ValueError(f"Unknown event type: {event_type}")

    # Return the cost, rounded to 4 decimal places for precision
    return round(cost_in_cents, 4)
