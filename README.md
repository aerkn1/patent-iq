# Patent IQ

## UI Runtime Split

1. [frontend_v1](frontend_v1/README.md) preserves the legacy UI.
2. [frontend_v2](frontend_v2/README.md) is the clean V2 implementation target.

## Backend Runtime Split

1. [backend](backend/README.md) is the preserved legacy/reference backend.
2. [backend_v2](backend_v2/README.md) is the clean V2 backend implementation target.

ML-based IP Evaluation Platform

## Overview

Patent IQ is an intelligent patent analysis system that leverages machine learning
to evaluate and analyze intellectual property.

This project uses automated semantic versioning and follows conventional commit standards.

## Features

- Semantic versioning with PEP 440 compliance
- Automated CI/CD workflows
- Branch protection and PR validation

## Development Workflow

See [VERSIONING.md](VERSIONING.md) for detailed development workflow and commit guidelines.

## Branches

- `dev` - Development/testing environment (version: X.Y.Z.dev0)
- `master` - Stable releases (version: X.Y.Z)
- `prod` - Production deployments (version: X.Y.Z)
