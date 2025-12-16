#!/Users/nealsanche/.claude/skills/show-moon-phase/venv/bin/python3
"""
Moon Phase Calculator with Detailed ASCII Art
Displays current moon phase, illumination, and location-specific data
"""

from skyfield.api import load, wgs84, utc
from skyfield import almanac
from datetime import datetime, timedelta
from math import cos, radians

def get_phase_name(angle):
    """Return phase name based on angle."""
    if angle < 22.5:
        return "New Moon"
    elif angle < 67.5:
        return "Waxing Crescent"
    elif angle < 112.5:
        return "First Quarter"
    elif angle < 157.5:
        return "Waxing Gibbous"
    elif angle < 202.5:
        return "Full Moon"
    elif angle < 247.5:
        return "Waning Gibbous"
    elif angle < 292.5:
        return "Last Quarter"
    elif angle < 337.5:
        return "Waning Crescent"
    else:
        return "New Moon"

def generate_moon_art(illumination, phase_angle):
    """Generate compact 5-line ASCII art based on moon phase."""
    is_waxing = phase_angle < 180

    if illumination < 5:  # New Moon
        return """
    .-------.
   (         )
   (         )
    '-------'
"""
    elif illumination < 25:  # Thin Crescent
        if is_waxing:
            return """
    .-------.
   ( ''      )
   ( ''      )
    '-------'
"""
        else:
            return """
    .-------.
   (      '' )
   (      '' )
    '-------'
"""
    elif illumination < 45:  # Larger Crescent
        if is_waxing:
            return """
    .-------.
   ( ''''    )
   ( ''''    )
    '-------'
"""
        else:
            return """
    .-------.
   (    '''' )
   (    '''' )
    '-------'
"""
    elif illumination < 55:  # Quarter
        if is_waxing:
            return """
    .-------.
   ( :::::   )
   ( :::::   )
    '-------'
"""
        else:
            return """
    .-------.
   (   ::::: )
   (   ::::: )
    '-------'
"""
    elif illumination < 75:  # Gibbous
        if is_waxing:
            return """
    .-------.
   ( ::::::::')
   ( ::::::::')
    '-------'
"""
        else:
            return """
    .-------.
   (':::::::: )
   (':::::::: )
    '-------'
"""
    else:  # Full Moon
        return """
    .-------.
   ( ::::::::)
   ( ::::::::)
    '-------'
"""

def main():
    import sys

    # Load ephemeris
    print("Loading astronomical data...")
    ts = load.timescale()
    eph = load('de421.bsp')

    earth = eph['earth']
    sun = eph['sun']
    moon = eph['moon']

    # Get location from command line or use defaults
    if len(sys.argv) >= 3:
        latitude = float(sys.argv[1])
        longitude = float(sys.argv[2])
        print(f"\nUsing location: {latitude}°, {longitude}°")
    else:
        # Default to Calgary, AB, Canada
        latitude = 51.0447
        longitude = -114.0719
        print(f"\nUsing default location: Calgary, AB, Canada ({latitude}°, {longitude}°)")
        print("(Run with: python moon_phase.py <latitude> <longitude> to specify location)\n")

    topos = wgs84.latlon(latitude, longitude)
    location = earth + topos

    # Current time (with timezone)
    now = datetime.now(utc)
    now_local = datetime.now()  # For display purposes
    t = ts.from_datetime(now)

    # Calculate phase
    e = earth.at(t)
    s = e.observe(sun).apparent()
    m = e.observe(moon).apparent()

    phase_angle = s.separation_from(m).degrees
    # Correct illumination formula: 0° = New Moon (0%), 180° = Full Moon (100%)
    illumination = 100 * (1 - cos(radians(phase_angle))) / 2

    # Calculate lunar age
    t0 = ts.from_datetime(now - timedelta(days=30))
    t1 = t
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))

    lunar_age = 0
    for time, phase in zip(times, phases):
        if phase == 0 and time.utc_datetime() < now:
            lunar_age = (now - time.utc_datetime()).days

    if lunar_age == 0:
        # Estimate if not found
        lunar_age = int(phase_angle / 360 * 29.53)

    phase_name = get_phase_name(phase_angle)

    # Calculate rise/set
    midnight = now_local.replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=utc)
    t0 = ts.from_datetime(midnight)
    t1 = ts.from_datetime(midnight + timedelta(days=1))

    f = almanac.risings_and_settings(eph, moon, topos)
    times, events = almanac.find_discrete(t0, t1, f)

    moonrise = "No moonrise today"
    moonset = "No moonset today"

    for time, event in zip(times, events):
        dt = time.utc_datetime().replace(tzinfo=None)
        if event:
            moonrise = dt.strftime("%I:%M %p")
        else:
            moonset = dt.strftime("%I:%M %p")

    # Find next events
    t0 = ts.from_datetime(now)
    t1 = ts.from_datetime(now + timedelta(days=60))
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))

    next_new_moon = "Not found"
    next_full_moon = "Not found"

    for time, phase in zip(times, phases):
        dt = time.utc_datetime()
        if phase == 0 and next_new_moon == "Not found" and dt > now:
            next_new_moon = dt.strftime("%B %d, %Y")
        elif phase == 2 and next_full_moon == "Not found" and dt > now:
            next_full_moon = dt.strftime("%B %d, %Y")

    # Generate art
    moon_art = generate_moon_art(illumination, phase_angle)

    # Display output
    print("\n" + "="*50)
    print("         LUNAR INFORMATION")
    print("="*50)
    print(moon_art)
    print("="*50)
    print(f"Phase:           {phase_name}")
    print(f"Illumination:    {illumination:.1f}%")
    print(f"Lunar Age:       Day {lunar_age} of lunar cycle")
    print(f"Phase Angle:     {phase_angle:.1f}°")
    print("="*50)
    print(f"Moonrise:        {moonrise}")
    print(f"Moonset:         {moonset}")
    print("="*50)
    print(f"Next New Moon:   {next_new_moon}")
    print(f"Next Full Moon:  {next_full_moon}")
    print("="*50)
    print(f"Date:            {now_local.strftime('%B %d, %Y')}")
    print(f"Time:            {now_local.strftime('%I:%M %p')}")
    print(f"Location:        {latitude:.4f}°, {longitude:.4f}°")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
