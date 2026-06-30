// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package invoker

import (
	"context"
	"encoding/json"
	"errors"
)

// ErrNotImplemented is returned by the scaffold invoker until OCI SDK integration is added.
var ErrNotImplemented = errors.New("oci functions invoker is not implemented")

// Target identifies the OCI Function to invoke.
type Target struct {
	Namespace      string
	FunctionName   string
	FunctionOCID   string
	InvokeEndpoint string
}

// Request contains one function invocation request.
type Request struct {
	Target Target
	Index  int32
	Body   json.RawMessage
}

// Response contains the result of one function invocation.
type Response struct {
	InvocationID string
	OCIRequestID string
	StatusCode   int32
	Body         json.RawMessage
}

// Interface hides OCI SDK details behind a narrow invocation contract.
type Interface interface {
	Invoke(ctx context.Context, request Request) (Response, error)
}

// FunctionIDRequirement is an optional capability for invokers that require a resolved OCI Function OCID.
type FunctionIDRequirement interface {
	RequiresFunctionID() bool
}

// NotImplemented is the default invoker used until OCI SDK support is implemented.
type NotImplemented struct{}

// Invoke returns ErrNotImplemented.
func (NotImplemented) Invoke(context.Context, Request) (Response, error) {
	return Response{}, ErrNotImplemented
}
