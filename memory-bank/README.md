---
title: Memory Bank - Project Knowledge Repository
version: 1.1
created: 2025-01-14
last_updated: 2025-07-15
---

# Power Importer Memory Bank

This memory bank serves as a comprehensive knowledge repository for the Power Importer project, designed to maintain continuity and context across development sessions.

## Purpose

The memory bank captures and preserves essential project knowledge including:
- Project objectives and business context
- Technical architecture and implementation details
- Current status and recent achievements
- Development patterns and best practices
- Progress tracking and future roadmap

## Memory Bank Structure

### Core Files

#### 1. `projectbrief.md` - Foundation Document
**Purpose**: Defines the project's core mission, scope, and success criteria
**Contents**:
- Project overview and purpose
- Key problems solved
- Primary stakeholders
- Success criteria and scope definition
- Current production-ready status

#### 2. `productContext.md` - Business Requirements
**Purpose**: Captures business needs, user experience, and operational requirements
**Contents**:
- Business problem definition
- Target user personas and journeys
- Business rules and processing logic
- Success metrics and compliance requirements
- Integration requirements

#### 3. `systemPatterns.md` - Technical Architecture
**Purpose**: Documents system design, patterns, and component relationships
**Contents**:
- High-level architecture and data flow
- Core design patterns (Pipeline, Strategy, Factory, etc.)
- Component relationships and responsibilities
- Performance and security patterns
- Testing and deployment patterns

#### 4. `techContext.md` - Implementation Details
**Purpose**: Technical implementation specifics and development environment
**Contents**:
- Technology stack and dependencies
- Environment configuration and setup
- API integration details and authentication
- Data processing algorithms
- Error handling and logging strategies

#### 5. `activeContext.md` - Current Work Focus
**Purpose**: Tracks current state, recent changes, and immediate priorities
**Contents**:
- Recent major achievements and bug fixes
- Current system capabilities and configuration
- Active development patterns and monitoring points
- Next steps and immediate priorities
- Known limitations and considerations

#### 6. `progress.md` - Status and Evolution
**Purpose**: Comprehensive progress tracking and milestone documentation
**Contents**:
- Completed major milestones and phases
- Current system capabilities and metrics
- Known issues and future enhancements
- Testing and quality assurance status
- Deployment readiness and next development priorities

## How to Use the Memory Bank

### For New Development Sessions
1. **Start with `projectbrief.md`** - Understand the project's core purpose
2. **Review `activeContext.md`** - Get current state and recent changes
3. **Check `progress.md`** - Understand what's completed and what's next
4. **Reference technical files** as needed for implementation details

### For Specific Tasks
- **Architecture Questions**: Consult `systemPatterns.md`
- **Business Logic**: Reference `productContext.md`
- **Technical Implementation**: Check `techContext.md`
- **Current Status**: Review `activeContext.md` and `progress.md`

### For Updates and Maintenance
- **After Major Changes**: Update `activeContext.md` and `progress.md`
- **New Features**: Update relevant technical and business context files
- **Bug Fixes**: Document in `activeContext.md` and track in `progress.md`
- **Architecture Changes**: Update `systemPatterns.md` and `techContext.md`

## Key Project Information Quick Reference

### Current Status
- **State**: Production Ready ✅
- **Last Major Update**: July 2025 (Environment Configuration Issue Resolution)
- **Performance**: 37.5% API call reduction, >99% success rate
- **Environment**: Production endpoints configured and verified, mixed environment issue resolved

### Core Technologies
- **Language**: Python 3.8+
- **Target System**: Microsoft Dynamics 365 Business Central
- **Authentication**: OAuth 2.0
- **Data Flow**: CSV → JSON → Business Central API

### Recent Achievements
1. **Production Endpoint Configuration**: Fixed hardcoded staging URLs
2. **VCT Responsibility Consolidation**: 37.5% API call reduction
3. **Environment Configuration Issue Resolution**: Eliminated mixed Production/Staging insertions (July 2025)
4. **Comprehensive Bug Fixes**: Authentication, currency, balance verification

### Key Components
- **Character Set Converter**: Japanese encoding handling
- **CSV to JSON Converter**: Data transformation pipeline
- **Process Japan Exports**: Main ERP integration orchestrator
- **OAuth Token Helper**: Authentication management
- **Exchange Rate API**: Currency conversion service

### Critical Success Factors
- **Environment Configuration**: Proper `BC_ENVIRONMENT` setting
- **Rate Limiting**: Respect Business Central API limits
- **Balance Verification**: Always verify debit/credit balance
- **Error Handling**: Comprehensive logging for compliance

## Maintenance Guidelines

### Regular Updates
- **Weekly**: Update `activeContext.md` with current work
- **After Major Features**: Update all relevant files
- **Monthly**: Review and update `progress.md`
- **Quarterly**: Comprehensive review of all files

### Version Control
- Each file includes version and last_updated metadata
- Track significant changes in file headers
- Maintain consistency across all memory bank files

### Quality Assurance
- Ensure all files remain current and accurate
- Cross-reference information between files
- Validate technical details against actual implementation
- Keep business context aligned with current requirements

## Integration with Development Workflow

### Planning Phase
- Use memory bank to understand current state
- Reference business requirements and technical constraints
- Plan changes considering existing patterns and architecture

### Implementation Phase
- Follow established patterns documented in `systemPatterns.md`
- Use technical details from `techContext.md` for implementation
- Maintain consistency with current configuration in `activeContext.md`

### Completion Phase
- Update `activeContext.md` with changes made
- Document new patterns or significant modifications
- Update `progress.md` with completed milestones
- Ensure all memory bank files remain current

This memory bank serves as the single source of truth for project knowledge, ensuring continuity and enabling effective development across all sessions and team members.
