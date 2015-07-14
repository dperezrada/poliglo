'use strict';

/**
 * @ngdoc service
 * @name poligloMonitorApp.Error
 * @description
 * # Error
 * Service in the poligloMonitorApp.
 */
angular.module('poligloMonitorApp')
  .service('Worker', function ($http, ENV) {
    var baseUrl = ENV.apiEndpoint+'/workers';

    var errors = function(worker, callback){
        var url = baseUrl+'/'+worker+'/errors';

        $http.get(url).
            success(callback);
    };

    return {
      errors: errors
    };

  });
