from datetime import datetime, timedelta

def compute_weekly_feedback_analytics(sessions):
    """
    Computes weekly satisfaction scores and comprehension breakdowns
    across sessions for visualization in the teacher section.
    """
    if not sessions:
        return {
            'has_data': False,
            'weekly_bars': [],
            'summary': {
                'overall_avg': 0.0,
                'total_responses': 0,
                'best_week': 'N/A',
                'best_score': 0.0,
                'trend': 'stable'
            }
        }

    # Filter sessions with responses and sort chronologically
    valid_sessions = [s for s in sessions if len(s.responses) > 0]
    valid_sessions.sort(key=lambda s: s.started_at)

    if not valid_sessions:
        return {
            'has_data': False,
            'weekly_bars': [],
            'summary': {
                'overall_avg': 0.0,
                'total_responses': 0,
                'best_week': 'N/A',
                'best_score': 0.0,
                'trend': 'stable'
            }
        }

    # If sessions span multiple days/weeks, label as Week 1, Week 2, etc.
    weekly_bars = []
    total_score_sum = 0
    total_resp_count = 0
    best_score = 0.0
    best_label = 'Week 1'

    for index, sess in enumerate(valid_sessions, start=1):
        responses = sess.responses
        count = len(responses)
        if count == 0:
            continue

        score_sum = sum(r.satisfaction for r in responses)
        avg_score = round(score_sum / count, 1)
        total_score_sum += score_sum
        total_resp_count += count

        # Percentage for CSS bar height (relative to 5.0 scale)
        height_pct = min(100, max(12, int((avg_score / 5.0) * 100)))

        # Understanding breakdown
        und_counts = {'understood': 0, 'partially': 0, 'needs_help': 0}
        for r in responses:
            if r.understanding in und_counts:
                und_counts[r.understanding] += 1
        
        und_pcts = {
            k: round((v / count * 100), 1) if count > 0 else 0
            for k, v in und_counts.items()
        }

        # Date formatting
        date_label = sess.started_at.strftime('%d %b')
        week_label = f"W{index}"

        if avg_score > best_score:
            best_score = avg_score
            best_label = f"{week_label} ({avg_score}/5)"

        weekly_bars.append({
            'session_id': sess.id,
            'session_token': sess.session_token,
            'class_code': sess.class_offering.course.code,
            'section_name': sess.class_offering.section.name,
            'week_label': week_label,
            'date_label': date_label,
            'full_label': f"{week_label} &bull; {date_label}",
            'avg_satisfaction': avg_score,
            'height_pct': height_pct,
            'response_count': count,
            'und_counts': und_counts,
            'und_pcts': und_pcts
        })

    overall_avg = round(total_score_sum / total_resp_count, 1) if total_resp_count > 0 else 0.0

    # Trend calculation
    trend = 'stable'
    if len(weekly_bars) >= 2:
        if weekly_bars[-1]['avg_satisfaction'] > weekly_bars[0]['avg_satisfaction']:
            trend = 'up'
        elif weekly_bars[-1]['avg_satisfaction'] < weekly_bars[0]['avg_satisfaction']:
            trend = 'down'

    return {
        'has_data': len(weekly_bars) > 0,
        'weekly_bars': weekly_bars,
        'summary': {
            'overall_avg': overall_avg,
            'total_responses': total_resp_count,
            'best_week': best_label,
            'best_score': best_score,
            'trend': trend
        }
    }
