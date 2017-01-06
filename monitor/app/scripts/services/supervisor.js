'use strict';

/**
 * @ngdoc service
 * @name poligloMonitorApp.Error
 * @description
 * # Error
 * Service in the poligloMonitorApp.
 */
angular.module('poligloMonitorApp')
  .service('Supervisor', function ($http, ENV) {
    var baseUrl = ENV.apiEndpoint+'/supervisor/';

    var status = function(callback, errorCallback){
      $http.get(baseUrl + 'status')
        .success(callback)
        .error(errorCallback);
    };

    var startProcess = function(processName, callback){
      $http.post(baseUrl + processName +'/start').
        success(callback);
    };

    var stopProcess = function(processName, callback){
      $http.post(baseUrl + processName +'/stop').
        success(callback);
    };

    return {
      status: status,
      startProcess: startProcess,
      stopProcess: stopProcess,
    };
  });
