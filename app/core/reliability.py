"""
Probabilistic Route Reliability Engine
Computes joint connection success probability across multi-hop train journeys:
P(Route Success) = P(Leg 1 on time) * P(Leg 2 catches | Leg 1 delay) * ...
"""

import math
from typing import List, Dict, Any, Tuple, Optional


def _normal_cdf(x: float, mean: float = 0.0, std: float = 1.0) -> float:
    """Standard Gaussian cumulative distribution function approximation."""
    if std <= 0:
        return 1.0 if x >= mean else 0.0
    z = (x - mean) / (std * math.sqrt(2.0))
    return 0.5 * (1.0 + math.erf(z))


def calculate_connection_probability(
    scheduled_changeover_min: int,
    min_walk_time_min: int = 15,
    predicted_delay_mean_min: float = 20.0,
    delay_variance_min: float = 25.0,
) -> float:
    """
    Computes the probability that an incoming train's delay will not cause
    a missed connection at a transfer junction.
    Available slack = scheduled_changeover - min_walk_time.
    P(success) = P(incoming_delay <= available_slack).
    """
    slack = scheduled_changeover_min - min_walk_time_min
    if slack <= 0:
        return 0.05  # Virtually impossible connection

    prob = _normal_cdf(
        x=slack,
        mean=predicted_delay_mean_min,
        std=delay_variance_min,
    )
    # Bound between 0.05 and 0.99
    return max(0.05, min(0.99, round(prob, 4)))


def compute_joint_route_reliability(
    legs: List[Dict[str, Any]],
    transfer_buffers_min: List[int],
    walk_times_min: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Calculates the joint multi-leg journey success probability.
    Returns individual connection probabilities, joint probability, and risk rating.
    """
    if not legs or len(legs) <= 1:
        # Direct train (0 transfers) has high baseline reliability
        single_leg_delay = legs[0].get("predicted_delay_min", 15) if legs else 15
        base_rel = 0.95 if single_leg_delay < 30 else 0.88
        return {
            "joint_reliability_score": base_rel,
            "joint_reliability_percent": f"{int(base_rel * 100)}%",
            "connection_probabilities": [],
            "risk_rating": "VERY_LOW" if base_rel >= 0.90 else "LOW",
        }

    num_transfers = len(legs) - 1
    walk_times = walk_times_min or [15] * num_transfers

    connection_probs = []
    joint_prob = 1.0

    for i in range(num_transfers):
        buffer_min = transfer_buffers_min[i] if i < len(transfer_buffers_min) else 45
        walk_min = walk_times[i] if i < len(walk_times) else 15
        pred_delay = float(legs[i].get("predicted_delay_min", 25))

        p_conn = calculate_connection_probability(
            scheduled_changeover_min=buffer_min,
            min_walk_time_min=walk_min,
            predicted_delay_mean_min=pred_delay,
            delay_variance_min=max(15.0, pred_delay * 0.6),
        )

        connection_probs.append({
            "transfer_index": i + 1,
            "station": legs[i].get("to_station", "JCT"),
            "buffer_minutes": buffer_min,
            "walk_minutes": walk_min,
            "predicted_incoming_delay": pred_delay,
            "success_probability": p_conn,
            "success_percent": f"{int(p_conn * 100)}%",
        })

        joint_prob *= p_conn

    joint_prob = round(joint_prob, 4)
    percent = int(joint_prob * 100)

    if percent >= 85:
        risk_rating = "VERY_LOW"
    elif percent >= 70:
        risk_rating = "MODERATE"
    elif percent >= 50:
        risk_rating = "HIGH"
    else:
        risk_rating = "CRITICAL"

    return {
        "joint_reliability_score": joint_prob,
        "joint_reliability_percent": f"{percent}%",
        "connection_probabilities": connection_probs,
        "risk_rating": risk_rating,
    }
