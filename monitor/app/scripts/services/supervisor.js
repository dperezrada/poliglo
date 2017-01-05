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

    var status = function(callback){
      $http.get(baseUrl + 'status').
        success(callback);
    };

    var startProcess = function(processName, callback){
      $http.get(baseUrl + processName +'/start').
        success(callback);
    };

    var stopProcess = function(processName, callback){
      $http.get(baseUrl + processName +'/stop').
        success(callback);
    };

    return {
      status: status,
      startProcess: startProcess,
      stopProcess: stopProcess,
    };
  });
