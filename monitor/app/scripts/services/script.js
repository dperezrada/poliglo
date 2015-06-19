'use strict';

/**
 * @ngdoc service
 * @name poligloMonitorApp.Script
 * @description
 * # Script
 * Service in the poligloMonitorApp.
 */
angular.module('poligloMonitorApp')
  .service('Script', function ($http, ENV) {
    var baseUrl = ENV.apiEndpoint;

    var list = function(byGroup, callback){
        var url = baseUrl+'/scripts';
        if(byGroup){
            url += '?by_group=1';
        }
        $http.get(url).
            success(callback);
    };
    var listProcesses = function(scriptType, callback){
        var url;
        if(scriptType){
            url = baseUrl+'/scripts/'+scriptType+'/processes';
        }

        $http.get(url).
            success(callback);
    };
    var get = function(scriptType, callback){
        var url = baseUrl+'/scripts/'+scriptType;
        $http.get(url).
            success(callback);
    };

    // Public API here
    return {
      list: list,
      listProcesses: listProcesses,
      get: get,
    };
    // AngularJS will instantiate a singleton by calling "new" on this function
  });
