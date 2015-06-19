'use strict';

/**
 * @ngdoc service
 * @name poligloMonitorApp.process
 * @description
 * # process
 * Service in the poligloMonitorApp.
 */
angular.module('poligloMonitorApp')
  .service('Process', function ($http, ENV) {
    var baseUrl = ENV.apiEndpoint;

    var get = function(processId, callback){
        var url = baseUrl+'/processes/'+processId;
        $http.get(url).
            success(callback);
    };
    var status = function(processId, callback){
        var url = baseUrl+'/processes/'+processId+'/status';
        $http.get(url).
            success(callback);
    };

    var stats = function(processId, callback){
        var url = baseUrl+'/processes/'+processId+'/stats';
        $http.get(url).
            success(callback);
    };
    var workerErrors = function(processId, workerId, callback){
        var url = baseUrl+'/processes/'+processId+'/workers/'+workerId+'/errors';
        $http.get(url).
            success(callback);
    };
    var workerFinalized = function(processId, workerId, callback){
        var url = baseUrl+'/processes/'+processId+'/workers/'+workerId+'/finalized';
        $http.get(url).
            success(callback);
    };
    var discardError = function(processId, workerId, redisErrorId, callback){
        var url = baseUrl+'/processes/'+processId+'/workers/'+workerId+'/errors/discard/'+redisErrorId;
        $http.get(url).
            success(callback);
    };
    var retryError = function(processId, workerId, redisErrorId, callback){
        var url = baseUrl+'/processes/'+processId+'/workers/'+workerId+'/errors/retry/'+redisErrorId;
        $http.get(url).
            success(callback);
    };
    var retryAllErrors = function(processId, workerId, callback){
        var url = baseUrl+'/processes/'+processId+'/workers/'+workerId+'/errors/retry/all';
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
