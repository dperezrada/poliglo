'use strict';

/**
 * @ngdoc overview
 * @name poligloMonitorApp
 * @description
 * # poligloMonitorApp
 *
 * Main module of the application.
 */
angular
  .module('poligloMonitorApp', ['ui.router', 'config', 'ngFlash'])
    .config(function($stateProvider, $urlRouterProvider) {
      //
      // For any unmatched url, redirect to /state1
      $urlRouterProvider.otherwise('/workflows');
      //
      // // Now set up the states
      $stateProvider
        .state('workflows', {
          templateUrl: 'views/partials/workflows.html',
        })
        .state('workflows.list', {
          url: '/workflows',
          templateUrl: 'views/partials/workflows.list.html',
          controller: 'WorkflowsListCtrl'
        })
        .state('workflows.listWorkflowInstances', {
          url: '/workflows/:workflow/workflow_instances?page',
          params: {
            page: {value: '1', squash: true}
          },
          templateUrl: 'views/partials/workflows.list_workflow_instances.html',
          controller: 'WorkflowInstancesListCtrl'
        })
        .state('workflowInstance', {
          templateUrl: 'views/partials/workflow_instance.html',
        })
        .state('workflowInstance.show', {
          url: '/workflow_instances/:workflowInstanceId',
          templateUrl: 'views/partials/workflow_instance.show.html',
          controller: 'WorkflowInstanceShowCtrl'
        })
        .state('workflowInstance.workerErrors', {
          url: '/workflow_instances/:workflowInstanceId/workers/:workerId/errors',
          templateUrl: 'views/partials/workflow_instance.worker_errors.html',
          controller: 'WorkflowInstanceWorkerErrorsCtrl'
        })
        .state('workflowInstance.workerFinalized', {
          url: '/workflow_instances/:workflowInstanceId/workers/:workerId/finalized',
          templateUrl: 'views/partials/workflow_instance.worker_finalized.html',
          controller: 'WorkflowInstanceWorkerFinalizedCtrl'
        })
        .state('supervisor', {
          url: '/supervisor/status',
          templateUrl: 'views/partials/supervisor.status.html',
          controller: 'SupervisorStatusCtrl'
        });

        // .state('workers', {
        //   templateUrl: 'views/partials/workflowInstance.html',
        // })
        // .state('workers.errors', {
        //   url: '/workers/:workerId/errors',
        //   templateUrl: 'views/partials/workers.errors.html',
        //   controller: 'WorkersErrorsCtrl'
        // });
    });
