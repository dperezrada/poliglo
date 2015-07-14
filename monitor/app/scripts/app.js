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
  .module('poligloMonitorApp', ['ui.router', 'config'])
    .config(function($stateProvider, $urlRouterProvider) {
      //
      // For any unmatched url, redirect to /state1
      $urlRouterProvider.otherwise('/scripts');
      //
      // Now set up the states
      $stateProvider
        .state('scripts', {
          templateUrl: 'views/partials/scripts.html',
        })
        .state('scripts.list', {
          url: '/scripts',
          templateUrl: 'views/partials/scripts.list.html',
          controller: 'ScriptsListCtrl'
        })
        .state('scripts.new', {
          url: '/scripts/new',
          templateUrl: 'views/partials/scripts.new.html',
          controller: 'ProcessesNewCtrl'
        })
        .state('scripts.list_processes', {
          url: '/scripts/:scriptType/processes',
          templateUrl: 'views/partials/scripts.list_processes.html',
          controller: 'ProcessesListCtrl'
        })
        .state('process', {
          templateUrl: 'views/partials/process.html',
        })
        .state('process.show', {
          url: '/process/:processId',
          templateUrl: 'views/partials/process.show.html',
          controller: 'ProcessShowCtrl'
        })
        .state('process.worker_errors', {
          url: '/process/:processId/workers/:workerId/errors',
          templateUrl: 'views/partials/process.worker_errors.html',
          controller: 'ProcessWorkerErrorsCtrl'
        })
        .state('process.worker_finalized', {
          url: '/process/:processId/workers/:workerId/finalized',
          templateUrl: 'views/partials/process.worker_finalized.html',
          controller: 'ProcessWorkerFinalizedCtrl'
        });

        // // .state('workers', {
        // //   templateUrl: 'views/partials/process.html',
        // // })
        // // .state('workers.errors', {
        // //   url: '/workers/:workerId/errors',
        // //   templateUrl: 'views/partials/workers.errors.html',
        // //   controller: 'WorkersErrorsCtrl'
        // // });
    });
