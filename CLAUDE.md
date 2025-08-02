# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ArkTwin is a distributed messaging framework for multi-agent systems like traffic simulators, digital twins, and city-scale co-simulations. It consists of two main components:

- **ArkTwin Center**: Message broker with network culling for large-scale agent transform messages
- **ArkTwin Edge**: Sidecar for agent-based software, handles coordinate transformation and time correction

## Architecture

The codebase is organized into four main modules:

- `arktwin/common/`: Shared protobuf definitions, data structures, and utilities
- `arktwin/center/`: Center server implementation with actor-based messaging (Atlas, Chart, Clock, Register actors)
- `arktwin/edge/`: Edge server implementation with REST API endpoints and gRPC connectors  
- `arktwin/e2e/`: End-to-end Gatling performance tests
- `arktwin/viewer/`: React/TypeScript frontend for neighbors visualization

## Key Commands

### Building

**Scala/Java components:**
```bash
cd arktwin
sbt center/assembly          # Build center JAR
sbt edge/assembly            # Build edge JAR  
sbt viewer/package edge/assembly  # Build viewer + edge JAR
```

**Viewer only:**
```bash
cd arktwin/viewer
npm install
npm run build
```

### Testing

```bash
cd arktwin
sbt test                     # Run all tests
sbt center/test              # Test center module only
sbt edge/test                # Test edge module only
sbt common/test              # Test common module only
```

**Single test:**
```bash
sbt "center/testOnly arktwin.center.actors.AtlasSpec"
```

### Development

**Formatting:**
```bash
sbt scalafmtAll              # Format Scala code
cd arktwin/viewer && npm run format  # Format TypeScript/React code
```

**Linting:**
```bash
sbt scalafix                 # Run Scalafix
cd arktwin/viewer && npm run format  # Biome check + format
```

**Generate OpenAPI specs:**
```bash
sbt edge/run generate-openapi-center > center-api.yaml
sbt edge/run generate-openapi-edge > edge-api.yaml  
```

### Running

**Development mode:**
```bash
# Terminal 1 - Center
sbt center/run

# Terminal 2 - Edge
ARKTWIN_CENTER_STATIC_HOST=localhost sbt edge/run

# Terminal 3 - Viewer dev server
cd arktwin/viewer && npm run dev
```

**Docker:**
```bash
docker build -t arktwin-center -f docker/center.dockerfile .
docker build -t arktwin-edge -f docker/edge.dockerfile .
```

## Key Technologies

- **Scala 3.7.1** with sbt 1.11.3
- **Apache Pekko** (typed actors, HTTP, gRPC streams)
- **Tapir** for REST API definition and OpenAPI generation  
- **ScalaPB** for Protocol Buffers
- **Kamon** for observability and Prometheus metrics
- **React 19 + TypeScript + Three.js** for viewer frontend

## Configuration

Configuration uses HOCON format via Typesafe Config. Key files:
- `arktwin/center/src/main/resources/reference.conf`
- `arktwin/edge/src/main/resources/reference.conf`

Environment variables can override settings (see README.md for full list).

## Protobuf Schema

All inter-service communication uses Protocol Buffers defined in `arktwin/common/src/main/protobuf/`. The schema includes coordinate transformations, timestamps, and gRPC service definitions for Center-Edge communication.