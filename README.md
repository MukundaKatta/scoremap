# SCOREMAP

AI Test Prep Coach with adaptive practice, performance analysis, and personalized study planning for standardized exams (SAT, GRE, GMAT).

## Features

- **Adaptive Practice** - Questions adjust in difficulty based on your performance
- **Performance Analysis** - Identify weak areas and track score trends over time
- **Study Planning** - Generate personalized study schedules targeting your weaknesses
- **Multiple Exams** - Full support for SAT, GRE, and GMAT with 20+ questions each
- **Timed Sessions** - Practice under realistic exam timing conditions

## Installation

```bash
pip install -e ".[dev]"
```

## Usage

### Practice

```bash
scoremap practice --exam sat --section math --count 10
```

### Analyze Performance

```bash
scoremap analyze --exam gre
```

### Generate Study Plan

```bash
scoremap plan --exam gmat --weeks 8
```

## Project Structure

```
scoremap/
  src/scoremap/
    cli.py          - Click CLI commands
    models.py       - Pydantic data models
    analyzer.py     - Performance analysis engine
    planner.py      - Personalized study planner
    report.py       - Rich terminal reports
    exams/          - Exam definitions (SAT, GRE, GMAT)
    practice/       - Adaptive practice engine
  tests/            - Test suite
  examples/         - Usage examples
```

## Author

Mukunda Katta
