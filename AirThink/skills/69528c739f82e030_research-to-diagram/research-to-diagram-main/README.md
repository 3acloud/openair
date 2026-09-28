# Research to Diagram

[English](README.md) | [中文](README_CN.md)

Deep research and auto-generate knowledge relationship diagrams in PDF format. From research to visualization in one integrated tool.

## The Problem

When you want to understand complex topics like:
- Literary character relationships (e.g., "Dream of the Red Chamber")
- Technical architectures (e.g., "Kubernetes architecture")
- Historical events (e.g., "Warring States period")
- Concept maps (e.g., "Machine learning algorithms")

You typically need to:
1. Spend hours researching across multiple sources
2. Manually organize information and structure relationships
3. Learn diagram tools like Graphviz, PlantUML
4. Design layouts and visual hierarchies
5. Generate and iterate on diagrams

**This takes hours or even days of work.**

## The Solution

`research-to-diagram` is a **research-driven knowledge visualization tool** that automates the entire process:

```
You provide: Topic/Research Question
           ↓
Skill handles: Research → Organize → Design → Generate
           ↓
You get: Professional PDF diagram + Reference sources
```

**Time saved: 10x faster** - from hours of work to 2-5 minutes of automated processing.

### Key Features

- ✅ **Auto Research**: Multi-round WebSearch for deep investigation
- ✅ **Smart Organization**: Automatic information extraction and structuring
- ✅ **Professional Design**: Choose optimal visualization based on topic
- ✅ **High-Quality Output**: Vector PDF diagrams with infinite zoom
- ✅ **Source Tracking**: Record all reference materials with links

### vs. structure-to-pdf

| Feature | research-to-diagram | structure-to-pdf |
|---------|---------------------|------------------|
| **Input** | Just a topic/question | Structured data required |
| **Research** | ✅ Automatic | ❌ None |
| **Use Case** | Knowledge exploration | Fast data conversion |
| **Time** | 2-5 minutes | <1 minute |
| **Sources** | ✅ Provides references | ❌ |

**Golden Rule**:
> No data? Use research-to-diagram. Have data? Use structure-to-pdf.

## Requirements

- **Graphviz**: `brew install graphviz` (macOS) or `apt-get install graphviz` (Linux)
- **Claude Code**: Built-in WebSearch capability
- **Internet**: For research and information gathering

## Installation

### Method 1: Git Clone (Recommended)

```bash
# Clone repository
git clone https://github.com/wshuyi/research-to-diagram.git

# Copy skill to Claude Code skills directory
cp -r research-to-diagram/skills/research-to-diagram ~/.claude/skills/

# Install Graphviz if not already installed
brew install graphviz
```

### Method 2: Plugin Marketplace

```bash
# Add plugin marketplace
/plugin marketplace add wshuyi/research-to-diagram

# Install skill
/plugin install research-to-diagram@wshuyi/research-to-diagram
```

## Usage

Simply describe your research topic to Claude Code using natural language:

### Example 1: Literary Character Relationships

```
Deep research "Dream of the Red Chamber" character relationships and generate a diagram PDF
```

**Output**:
- 50+ characters mapped
- 7 family clusters
- Multiple relationship types (blood, marriage, alliance)
- 152KB professional PDF
- 7 authoritative sources

### Example 2: Technical Architecture

```
Research Kubernetes architecture and generate a visualization diagram
```

**Expected output**:
- Control plane components
- Data plane components
- Plugin ecosystem
- Component interactions

### Example 3: Historical Analysis

```
Analyze Warring States period country relationships and create a relationship diagram
```

**Expected output**:
- Seven major states
- Alliance strategies (Vertical & Horizontal alliances)
- Major battles
- Unification timeline

## How It Works

The skill follows a systematic workflow:

```
1. Task Planning (TodoWrite)
   ↓
2. Deep Research Phase
   - Multiple WebSearch rounds
   - Information source recording
   - Knowledge extraction
   ↓
3. Structure Design Phase
   - Choose diagram type
   - Design hierarchy
   - Plan visual layout
   ↓
4. Visualization Implementation
   - Generate Graphviz DOT
   - Configure styles
   - Optimize layout
   ↓
5. PDF Generation
   - Compile to vector PDF
   - Verify output quality
   ↓
6. Documentation
   - Provide reference sources
   - Generate installation guide
```

## Diagram Types

### Character Relationship Diagrams
- Family trees and genealogies
- Social networks
- Organizational structures

**Template**: `examples/character_relationships.dot`

### Concept Maps
- Knowledge classification
- Hierarchical concepts
- Mind maps

**Template**: `examples/concept_map.dot`

### Technical Architecture
- System components
- Dependency relationships
- Layered architectures

**Template**: `examples/tech_architecture.dot`

## Output Files

Generated files are saved to `~/` or user-specified directory:

- `<topic>_relations.dot` - Graphviz source file
- `<topic>_relations.pdf` - Final PDF diagram
- `<topic>_sources.md` - Reference materials (optional)

## Advanced Features

### Custom Layout Direction

```
Research company development history and generate timeline diagram (left-to-right layout)
```

### Specify Detail Level

```
Quick research on React Hooks and generate simple diagram
```

```
Deep research React Hooks implementation principles and generate detailed diagram
```

### Specify Output Location

```
Research quantum computing history and generate diagram, save to ~/Documents/
```

## FAQ

**Q: How long does it take?**
A: Typically 2-5 minutes, depending on topic complexity and research depth.

**Q: Is the research information accurate?**
A: The skill:
- Cross-validates from multiple sources
- Provides all reference links
- Uses latest WebSearch results

**Q: Can I modify the generated diagram?**
A: Yes! The `.dot` source file can be edited manually:
```
Modify hongloumeng_relations.dot to add more relationship details
```

**Q: Can I generate other formats?**
A: Yes:
```
Generate PNG image version
Generate both PDF and SVG formats
```

**Q: What if the diagram is too complex?**
A: Request step-by-step generation:
```
First generate main character and family overview diagram,
then we can drill down into specific family details
```

## Examples

See [USAGE_EXAMPLES.md](skills/research-to-diagram/USAGE_EXAMPLES.md) for 7 detailed examples including:
- Literary works
- Technical concepts
- Historical events
- Biological classification
- Geographic relationships
- And more...

## Documentation

- [SKILL.md](skills/research-to-diagram/SKILL.md) - Core skill instructions
- [README.md](skills/research-to-diagram/README.md) - Complete usage guide
- [COMPARISON.md](skills/research-to-diagram/COMPARISON.md) - vs. structure-to-pdf comparison
- [USAGE_EXAMPLES.md](skills/research-to-diagram/USAGE_EXAMPLES.md) - Detailed examples

## Contributing

Contributions welcome! Please feel free to submit:
- New diagram templates
- Best practice examples
- Bug reports
- Feature requests

## License

MIT License - see [LICENSE](LICENSE) for details

## Author

Created by [wshuyi](https://github.com/wshuyi)

Built with [Claude Code](https://claude.com/claude-code)

## Acknowledgments

- Based on experience from the "Dream of the Red Chamber" character relationship project
- Inspired by the need for efficient knowledge visualization
- Thanks to the Graphviz community for excellent diagram tools
