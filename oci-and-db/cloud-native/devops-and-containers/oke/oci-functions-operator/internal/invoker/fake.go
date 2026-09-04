// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package invoker

import (
	"context"
	"fmt"
)

// Fake is a deterministic invoker for local development and controller tests.
type Fake struct{}

// Invoke returns a successful fake invocation response.
func (Fake) Invoke(_ context.Context, request Request) (Response, error) {
	return Response{
		InvocationID: fmt.Sprintf("fake-%s-%d", request.Target.FunctionName, request.Index),
		StatusCode:   202,
	}, nil
}
