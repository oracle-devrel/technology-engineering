// Copyright 2026.
// SPDX-License-Identifier: Apache-2.0

package main

import (
	"flag"
	"os"

	functionsv1alpha1 "github.com/oracle/oci-functions-operator/api/v1alpha1"
	"github.com/oracle/oci-functions-operator/internal/controller"
	"k8s.io/apimachinery/pkg/runtime"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	clientgoscheme "k8s.io/client-go/kubernetes/scheme"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/healthz"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	metricsserver "sigs.k8s.io/controller-runtime/pkg/metrics/server"
)

var scheme = runtime.NewScheme()

func init() {
	utilruntime.Must(clientgoscheme.AddToScheme(scheme))
	utilruntime.Must(functionsv1alpha1.AddToScheme(scheme))
}

func main() {
	var metricsAddr string
	var enableLeaderElection bool
	var probeAddr string

	flag.StringVar(&metricsAddr, "metrics-bind-address", ":8080", "The address the metric endpoint binds to.")
	flag.StringVar(&probeAddr, "health-probe-bind-address", ":8081", "The address the probe endpoint binds to.")
	flag.BoolVar(&enableLeaderElection, "leader-elect", false, "Enable leader election for controller manager.")
	opts := zap.Options{Development: true}
	opts.BindFlags(flag.CommandLine)
	flag.Parse()

	ctrl.SetLogger(zap.New(zap.UseFlagOptions(&opts)))
	setupLog := ctrl.Log.WithName("setup")

	selectedInvoker, invokerMode, err := selectInvoker(os.Getenv(invokerModeEnv))
	if err != nil {
		setupLog.Error(err, "unable to configure invoker")
		os.Exit(1)
	}
	setupLog.Info("configured invoker", "mode", invokerMode)

	functionManager, err := selectLifecycleManager(invokerMode)
	if err != nil {
		setupLog.Error(err, "unable to configure Function lifecycle manager")
		os.Exit(1)
	}
	eventTriggerManager, err := selectEventTriggerManager(invokerMode)
	if err != nil {
		setupLog.Error(err, "unable to configure FunctionEventTrigger manager")
		os.Exit(1)
	}

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
		Metrics: metricsserver.Options{
			BindAddress: metricsAddr,
		},
		HealthProbeBindAddress: probeAddr,
		LeaderElection:         enableLeaderElection,
		LeaderElectionID:       "oci-functions-operator.functions.oci.oracle.com",
	})
	if err != nil {
		setupLog.Error(err, "unable to start manager")
		os.Exit(1)
	}

	if err = (&controller.FunctionReconciler{
		Client:   mgr.GetClient(),
		Scheme:   mgr.GetScheme(),
		Manager:  functionManager,
		Recorder: mgr.GetEventRecorderFor("function-controller"),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "Function")
		os.Exit(1)
	}

	if err = (&controller.FunctionJobReconciler{
		Client:   mgr.GetClient(),
		Scheme:   mgr.GetScheme(),
		Invoker:  selectedInvoker,
		Recorder: mgr.GetEventRecorderFor("functionjob-controller"),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "FunctionJob")
		os.Exit(1)
	}

	if err = (&controller.FunctionEventReconciler{
		Client:   mgr.GetClient(),
		Scheme:   mgr.GetScheme(),
		Invoker:  selectedInvoker,
		Recorder: mgr.GetEventRecorderFor("functionevent-controller"),
	}).SetupWithManager(mgr); err != nil {
		setupLog.Error(err, "unable to create controller", "controller", "FunctionEvent")
		os.Exit(1)
	}

	if eventTriggerManager != nil {
		if err = (&controller.FunctionEventTriggerReconciler{
			Client:   mgr.GetClient(),
			Scheme:   mgr.GetScheme(),
			Manager:  eventTriggerManager,
			Recorder: mgr.GetEventRecorderFor("functioneventtrigger-controller"),
		}).SetupWithManager(mgr); err != nil {
			setupLog.Error(err, "unable to create controller", "controller", "FunctionEventTrigger")
			os.Exit(1)
		}
	} else {
		setupLog.Info("skipping FunctionEventTrigger controller because OCI Events manager is not configured", "mode", invokerMode)
	}

	if err := mgr.AddHealthzCheck("healthz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up health check")
		os.Exit(1)
	}
	if err := mgr.AddReadyzCheck("readyz", healthz.Ping); err != nil {
		setupLog.Error(err, "unable to set up ready check")
		os.Exit(1)
	}

	setupLog.Info("starting manager")
	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		setupLog.Error(err, "problem running manager")
		os.Exit(1)
	}
}
