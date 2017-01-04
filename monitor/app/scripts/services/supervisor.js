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
    var baseUrl = ENV.apiEndpoint+'/supervisor';

    var status = function(callback){
        $http.get(baseUrl).
            success(callback);
    };

    return {status: status};
  });
