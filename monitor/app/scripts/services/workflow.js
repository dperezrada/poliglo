'use strict';

/**
 * @ngdoc service
 * @name poligloMonitorApp.Workflow
 * @description
 * # Workflow
 * Service in the poligloMonitorApp.
 */
angular.module('poligloMonitorApp')
  .service('Workflow', function ($http, ENV) {
    var baseUrl = ENV.apiEndpoint;

    var list = function(byGroup, callback){
        var url = baseUrl+'/workflows';
        if(byGroup){
            url += '?by_group=1';
        }
        $http.get(url).
            success(callback);
    };
    var listWorkflowInstances = function(workflow, callback){
        var url;
        if(workflow){
            url = baseUrl+'/workflows/'+workflow+'/workflow_instances';
        }

        $http.get(url).
            success(callback);
    };
    var get = function(workflow, callback){
        var url = baseUrl+'/workflows/'+workflow;
        $http.get(url).
            success(callback);
    };

    // Public API here
    return {
      list: list,
      listWorkflowInstances: listWorkflowInstances,
      get: get,
    };
    // AngularJS will instantiate a singleton by calling "new" on this function
  });
