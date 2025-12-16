---
name: show-moon-phase
description: Display current moon phase with detailed ASCII art visualization, illumination percentage, lunar age, next moon events, and location-specific moonrise/moonset times. Use when user asks about the moon, moon phase, lunar calendar, or wants to see what the moon looks like today.
---

<objective>
Calculate and display comprehensive lunar information including current phase, detailed ASCII art visualization, illumination percentage, lunar age, upcoming moon events, and location-specific rise/set times using the Skyfield astronomy library.
</objective>

<quick_start>
<basic_usage>
**Virtual environment required** (macOS/modern Linux block system pip installs):
```bash
python3 -m venv ~/.venvs/moon-phase && source ~/.venvs/moon-phase/bin/activate && pip install skyfield
```

For subsequent runs, activate the existing venv:
```bash
source ~/.venvs/moon-phase/bin/activate
```

Calculate current moon phase:
```python
from skyfield.api import load
from datetime import datetime

# Load ephemeris data
ts = load.timescale()
eph = load('de421.bsp')

# Current time
t = ts.now()

# Get sun and moon positions
earth = eph['earth']
sun = eph['sun']
moon = eph['moon']

# Calculate phase angle
e = earth.at(t)
s = e.observe(sun).apparent()
m = e.observe(moon).apparent()

# Phase angle in degrees (0° = New, 180° = Full)
phase_angle = s.separation_from(m).degrees

# Illumination percentage
illumination = 100 * (1 - cos(radians(phase_angle))) / 2
```

This gives you the phase angle and illumination percentage.
</basic_usage>

<comprehensive_output>
For full details with ASCII art, location data, and next events, use the complete workflow below.
</comprehensive_output>
</quick_start>

<workflow>
<step_1 name="setup_and_data_loading">
**Setup virtual environment and install dependencies:**

```bash
# Create and activate venv (required on macOS/modern Linux)
python3 -m venv ~/.venvs/moon-phase
source ~/.venvs/moon-phase/bin/activate
pip install skyfield
```

**Note**: Modern systems use PEP 668 externally-managed environments. Always use a venv for Python dependencies.

```python
from skyfield.api import load, wgs84
from skyfield import almanac
from datetime import datetime, timedelta
from math import cos, radians
import sys

# Load timescale and ephemeris
ts = load.timescale()
eph = load('de421.bsp')  # JPL ephemeris data

# Get celestial bodies
earth = eph['earth']
sun = eph['sun']
moon = eph['moon']
```

**Note**: First run downloads ephemeris data (~10MB). Subsequent runs use cached data.
</step_1>

<step_2 name="get_location">
**Get user's location for rise/set times:**

```python
# Option 1: Ask user for location
latitude = float(input("Enter latitude (e.g., 37.7749): "))
longitude = float(input("Enter longitude (e.g., -122.4194): "))

# Option 2: Use default location (e.g., user's city)
# San Francisco example:
# latitude, longitude = 37.7749, -122.4194

# Create observer location
location = earth + wgs84.latlon(latitude, longitude)
```
</step_2>

<step_3 name="calculate_phase">
**Calculate current moon phase and illumination:**

```python
# Current time
now = datetime.now()
t = ts.from_datetime(now)

# Observe sun and moon from Earth
e = earth.at(t)
s = e.observe(sun).apparent()
m = e.observe(moon).apparent()

# Calculate phase angle (0° = New Moon, 180° = Full Moon)
phase_angle = s.separation_from(m).degrees

# Calculate illumination percentage
illumination = 100 * (1 + cos(radians(phase_angle))) / 2

# Calculate lunar age (days since new moon)
# Use almanac to find previous new moon
t0 = ts.from_datetime(now - timedelta(days=30))
t1 = ts.from_datetime(now)
times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))

# Find most recent new moon (phase 0)
new_moon_time = None
for time, phase in zip(times, phases):
    if phase == 0 and time.utc_datetime() < now:
        new_moon_time = time

if new_moon_time:
    lunar_age = (now - new_moon_time.utc_datetime()).days
else:
    # Estimate if not found in last 30 days
    lunar_age = int(phase_angle / 360 * 29.53)

# Determine phase name
def get_phase_name(angle):
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

phase_name = get_phase_name(phase_angle)
```
</step_3>

<step_4 name="calculate_rise_set">
**Calculate moonrise and moonset times:**

```python
from skyfield import almanac

# Define time range for today
midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
t0 = ts.from_datetime(midnight)
t1 = ts.from_datetime(midnight + timedelta(days=1))

# Find rise and set times
f = almanac.risings_and_settings(eph, moon, location)
times, events = almanac.find_discrete(t0, t1, f)

moonrise = None
moonset = None

for time, event in zip(times, events):
    dt = time.utc_datetime().replace(tzinfo=None)
    if event:  # 1 = rise
        moonrise = dt.strftime("%I:%M %p")
    else:  # 0 = set
        moonset = dt.strftime("%I:%M %p")

if not moonrise:
    moonrise = "No moonrise today"
if not moonset:
    moonset = "No moonset today"
```
</step_4>

<step_5 name="find_next_events">
**Find next full moon and new moon:**

```python
# Search next 60 days for moon phases
t0 = ts.from_datetime(now)
t1 = ts.from_datetime(now + timedelta(days=60))
times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))

next_new_moon = None
next_full_moon = None

for time, phase in zip(times, phases):
    dt = time.utc_datetime()
    if phase == 0 and not next_new_moon and dt > now:
        next_new_moon = dt.strftime("%B %d, %Y")
    elif phase == 2 and not next_full_moon and dt > now:
        next_full_moon = dt.strftime("%B %d, %Y")

    if next_new_moon and next_full_moon:
        break
```
</step_5>

<step_6 name="generate_ascii_art">
**Generate detailed ASCII art based on phase:**

```python
def generate_moon_art(illumination, phase_angle):
    """
    Generate detailed ASCII art (15 lines) showing moon phase.
    Uses different characters for shading and illumination.
    """

    # Determine if waxing or waning
    is_waxing = phase_angle < 180

    # Moon templates with different illumination levels
    if illumination < 5:  # New Moon
        return """
       .----------.
     (              )
    (                )
   (                  )
   (                  )
   (                  )
   (                  )
   (                  )
    (                )
     (              )
       '----------'
"""

    elif illumination < 25:  # Thin Crescent
        if is_waxing:  # Right side lit
            return """
       .----------.
     ( '''           )
    (  '''            )
   (   '''             )
   (   '''             )
   (   '''             )
   (   '''             )
   (   '''             )
    (  '''            )
     ( '''           )
       '----------'
"""
        else:  # Left side lit (waning)
            return """
       .----------.
     (           ''' )
    (            '''  )
   (             '''   )
   (             '''   )
   (             '''   )
   (             '''   )
   (             '''   )
    (            '''  )
     (           ''' )
       '----------'
"""

    elif illumination < 45:  # Larger Crescent
        if is_waxing:
            return """
       .----------.
     ( '''''         )
    (  '''''          )
   (   '''''           )
   (   '''''           )
   (   '''''           )
   (   '''''           )
   (   '''''           )
    (  '''''          )
     ( '''''         )
       '----------'
"""
        else:
            return """
       .----------.
     (         ''''' )
    (          '''''  )
   (           '''''   )
   (           '''''   )
   (           '''''   )
   (           '''''   )
   (           '''''   )
    (          '''''  )
     (         ''''' )
       '----------'
"""

    elif illumination < 55:  # First/Last Quarter
        if is_waxing:  # Right half lit
            return """
       .----------.
     ( :::::::       )
    (  :::::::        )
   (   :::::::         )
   (   :::::::         )
   (   :::::::         )
   (   :::::::         )
   (   :::::::         )
    (  :::::::        )
     ( :::::::       )
       '----------'
"""
        else:  # Left half lit
            return """
       .----------.
     (       :::::::)
    (        :::::::  )
   (         :::::::   )
   (         :::::::   )
   (         :::::::   )
   (         :::::::   )
   (         :::::::   )
    (        :::::::  )
     (       :::::::)
       '----------'
"""

    elif illumination < 75:  # Gibbous
        if is_waxing:
            return """
       .----------.
     ( :::::::::::'' )
    (  :::::::::::''  )
   (   :::::::::::''   )
   (   :::::::::::''   )
   (   :::::::::::''   )
   (   :::::::::::''   )
   (   :::::::::::''   )
    (  :::::::::::''  )
     ( :::::::::::'' )
       '----------'
"""
        else:
            return """
       .----------.
     ( '':::::::::::)
    (  '':::::::::::  )
   (   '':::::::::::   )
   (   '':::::::::::   )
   (   '':::::::::::   )
   (   '':::::::::::   )
   (   '':::::::::::   )
    (  '':::::::::::  )
     ( '':::::::::::)
       '----------'
"""

    else:  # Full Moon
        return """
       .----------.
     ( :::::::::::: )
    (  ::::::::::::  )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
    (  ::::::::::::  )
     ( :::::::::::: )
       '----------'
"""

# Generate the art
moon_art = generate_moon_art(illumination, phase_angle)
```
</step_6>

<step_7 name="display_output">
**Format and display comprehensive output:**

```python
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
print(f"Date:            {now.strftime('%B %d, %Y')}")
print(f"Time:            {now.strftime('%I:%M %p')}")
print("="*50 + "\n")
```
</step_7>
</workflow>

<complete_script>
**Complete standalone script:**

Save as `moon_phase.py` and run with `python moon_phase.py`:

```python
#!/usr/bin/env python3
"""
Moon Phase Calculator with Detailed ASCII Art
Displays current moon phase, illumination, and location-specific data
"""

from skyfield.api import load, wgs84
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
    """Generate ASCII art based on moon phase."""
    is_waxing = phase_angle < 180

    if illumination < 5:
        return """
       .----------.
     (              )
    (                )
   (                  )
   (                  )
   (                  )
   (                  )
   (                  )
    (                )
     (              )
       '----------'
"""
    elif illumination < 25:
        if is_waxing:
            return """
       .----------.
     ( '''           )
    (  '''            )
   (   '''             )
   (   '''             )
   (   '''             )
   (   '''             )
   (   '''             )
    (  '''            )
     ( '''           )
       '----------'
"""
        else:
            return """
       .----------.
     (           ''' )
    (            '''  )
   (             '''   )
   (             '''   )
   (             '''   )
   (             '''   )
   (             '''   )
    (            '''  )
     (           ''' )
       '----------'
"""
    elif illumination < 45:
        if is_waxing:
            return """
       .----------.
     ( '''''         )
    (  '''''          )
   (   '''''           )
   (   '''''           )
   (   '''''           )
   (   '''''           )
   (   '''''           )
    (  '''''          )
     ( '''''         )
       '----------'
"""
        else:
            return """
       .----------.
     (         ''''' )
    (          '''''  )
   (           '''''   )
   (           '''''   )
   (           '''''   )
   (           '''''   )
   (           '''''   )
    (          '''''  )
     (         ''''' )
       '----------'
"""
    elif illumination < 55:
        if is_waxing:
            return """
       .----------.
     ( :::::::       )
    (  :::::::        )
   (   :::::::         )
   (   :::::::         )
   (   :::::::         )
   (   :::::::         )
   (   :::::::         )
    (  :::::::        )
     ( :::::::       )
       '----------'
"""
        else:
            return """
       .----------.
     (       :::::::)
    (        :::::::  )
   (         :::::::   )
   (         :::::::   )
   (         :::::::   )
   (         :::::::   )
   (         :::::::   )
    (        :::::::  )
     (       :::::::)
       '----------'
"""
    elif illumination < 75:
        if is_waxing:
            return """
       .----------.
     ( :::::::::::'' )
    (  :::::::::::''  )
   (   :::::::::::''   )
   (   :::::::::::''   )
   (   :::::::::::''   )
   (   :::::::::::''   )
   (   :::::::::::''   )
    (  :::::::::::''  )
     ( :::::::::::'' )
       '----------'
"""
        else:
            return """
       .----------.
     ( '':::::::::::)
    (  '':::::::::::  )
   (   '':::::::::::   )
   (   '':::::::::::   )
   (   '':::::::::::   )
   (   '':::::::::::   )
   (   '':::::::::::   )
    (  '':::::::::::  )
     ( '':::::::::::)
       '----------'
"""
    else:
        return """
       .----------.
     ( :::::::::::: )
    (  ::::::::::::  )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
   (   ::::::::::::::   )
    (  ::::::::::::  )
     ( :::::::::::: )
       '----------'
"""

def main():
    # Load ephemeris
    ts = load.timescale()
    eph = load('de421.bsp')

    earth = eph['earth']
    sun = eph['sun']
    moon = eph['moon']

    # Get location (default to San Francisco)
    print("Enter your location (or press Enter for default):")
    lat_input = input("Latitude (default 37.7749): ").strip()
    lon_input = input("Longitude (default -122.4194): ").strip()

    latitude = float(lat_input) if lat_input else 37.7749
    longitude = float(lon_input) if lon_input else -122.4194

    location = earth + wgs84.latlon(latitude, longitude)

    # Current time
    now = datetime.now()
    t = ts.from_datetime(now)

    # Calculate phase
    e = earth.at(t)
    s = e.observe(sun).apparent()
    m = e.observe(moon).apparent()

    phase_angle = s.separation_from(m).degrees
    illumination = 100 * (1 + cos(radians(phase_angle))) / 2

    # Calculate lunar age
    t0 = ts.from_datetime(now - timedelta(days=30))
    t1 = ts.from_datetime(now)
    times, phases = almanac.find_discrete(t0, t1, almanac.moon_phases(eph))

    lunar_age = 0
    for time, phase in zip(times, phases):
        if phase == 0 and time.utc_datetime() < now:
            lunar_age = (now - time.utc_datetime()).days

    phase_name = get_phase_name(phase_angle)

    # Calculate rise/set
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    t0 = ts.from_datetime(midnight)
    t1 = ts.from_datetime(midnight + timedelta(days=1))

    f = almanac.risings_and_settings(eph, moon, location)
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
        if phase == 0 and not next_new_moon == "Not found" and dt > now:
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
    print(f"Date:            {now.strftime('%B %d, %Y')}")
    print(f"Time:            {now.strftime('%I:%M %p')}")
    print(f"Location:        {latitude:.4f}°, {longitude:.4f}°")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
```
</complete_script>

<location_handling>
**Getting user location:**

The script needs latitude/longitude for accurate rise/set times. Options:

1. **Prompt user** (implemented in complete script above)
2. **Use IP geolocation** (requires additional library like `geocoder`)
3. **Read from config file** (save user's location for reuse)
4. **Command line arguments**: `python moon_phase.py --lat 37.7749 --lon -122.4194`

**Common US cities (for testing):**
- San Francisco: 37.7749, -122.4194
- New York: 40.7128, -74.0060
- Chicago: 41.8781, -87.6298
- Los Angeles: 34.0522, -118.2437
- Miami: 25.7617, -80.1918
</location_handling>

<ascii_art_legend>
**Character meanings in ASCII art:**
- `.`, `'`, `(`, `)`, `-` : Moon outline/border
- `'` : Partial illumination (crescent)
- `:` : Full illumination (visible surface)
- Empty space : Dark/shadow area

**Phase progression:**
1. New Moon: Empty circle
2. Waxing Crescent: Thin bright strip on right
3. First Quarter: Right half bright
4. Waxing Gibbous: Mostly bright, small shadow on left
5. Full Moon: Fully bright
6. Waning Gibbous: Mostly bright, small shadow on right
7. Last Quarter: Left half bright
8. Waning Crescent: Thin bright strip on left
</ascii_art_legend>

<troubleshooting>
**Issue: "ModuleNotFoundError: No module named 'skyfield'"**
- Solution: Run `pip install skyfield` (within an activated venv)

**Issue: "error: externally-managed-environment"**
- Cause: macOS/modern Linux block system-wide pip installs (PEP 668)
- Solution: Use a virtual environment:
  ```bash
  python3 -m venv ~/.venvs/moon-phase
  source ~/.venvs/moon-phase/bin/activate
  pip install skyfield
  ```

**Issue: First run takes long time**
- Cause: Downloading ephemeris data (~10MB)
- Solution: Wait for download to complete. Subsequent runs are instant.

**Issue: "No moonrise today" or "No moonset today"**
- Cause: At high latitudes, moon may not rise or set every day
- This is normal and accurate behavior

**Issue: Inaccurate times**
- Check latitude/longitude are correct
- Ensure your system time/timezone is correct
- Skyfield uses UTC internally and converts appropriately

**Issue: Phase angle seems wrong**
- Verify ephemeris file is downloaded correctly
- Try deleting cached files and re-running to re-download
</troubleshooting>

<enhancements>
**Possible additions:**
- Moon distance (apogee/perigee)
- Zodiac sign
- Eclipses information
- Supermoon detection
- Color-coded output (using ANSI colors)
- Export to image format
- Multiple moon art styles
- Lunar calendar view (full month)
</enhancements>

<success_criteria>
The skill succeeds when:
- Current moon phase name is displayed correctly
- ASCII art accurately represents the phase (crescent orientation, illumination amount)
- Illumination percentage matches phase (0% new, 50% quarter, 100% full)
- Lunar age is within 0-29 days
- Moonrise/moonset times are shown (or "No moonrise/moonset" if appropriate)
- Next full and new moon dates are within next 60 days
- Output is visually clear and well-formatted
- Location-specific data reflects user's coordinates
</success_criteria>
