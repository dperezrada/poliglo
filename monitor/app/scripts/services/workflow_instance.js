'use strict';

/**
 * @ngdoc service
 * @name poligloMonitorApp.workflow_instance
 * @description
 * # workflow_instance
 * Service in the poligloMonitorApp.
 */
angular.module('poligloMonitorApp')
  .service('WorkflowInstance', function ($http, ENV) {
    var baseUrl = ENV.apiEndpoint;

    var get = function(workflowInstanceId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId;
        $http.get(url).
            success(callback);
    };
    var status = function(workflowInstanceId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/status';
        $http.get(url).
            success(callback);
    };

    var stats = function(workflowInstanceId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/stats';
        $http.get(url).
            success(callback);
    };
    var workerErrors = function(workflowInstanceId, workerId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/workers/'+workerId+'/errors';
        $http.get(url).
            success(callback);
    };
    var workerFinalized = function(workflowInstanceId, workerId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/workers/'+workerId+'/finalized';
        $http.get(url).
            success(callback);
    };
    var discardError = function(workflowInstanceId, workerId, redisErrorId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/workers/'+workerId+'/errors/discard/'+redisErrorId;
        $http.get(url).
            success(callback);
    };
    var retryError = function(workflowInstanceId, workerId, redisErrorId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/workers/'+workerId+'/errors/retry/'+redisErrorId;
        $http.get(url).
            success(callback);
    };
    var retryAllErrors = function(workflowInstanceId, workerId, callback){
        var url = baseUrl+'/workflow_instances/'+workflowInstanceId+'/workers/'+workerId+'/errors/retry/all';
        $http.get(url).
            success(callback);
    };

    // Public API here
    return {
      get: get,
      status: status,
      stats: stats,
      workerErrors: workerErrors,
      workerFinalized: workerFinalized,
      discardError: discardError,
      retryError: retryError,
      retryAllErrors: retryAllErrors
    };
  });
