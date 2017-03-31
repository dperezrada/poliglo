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

    var list = function(byGroup, callback, error_callback){
        var url = baseUrl+'/workflows';
        if(byGroup){
            url += '?by_group=1';
        }
        $http.get(url)
            .success(callback)
            .error(error_callback);
    };
    var listWorkflowInstances = function(workflow, page, callback){
        var url = baseUrl+'/workflows/'+workflow+'/workflow_instances?page='+page;
        $http.get(url).
            success(callback);
    };
    var supervisorStatus = function(workflow, callback){
        var url;
        if(workflow){
            url = baseUrl+'/workflows/'+workflow+'/supervisor/status';
        }
        $http.get(url).
            success(callback);
    }
    var supervisorStart = function(workflow, callback){
        var url;
        if(workflow){
            url = baseUrl+'/workflows/'+workflow+'/supervisor/start';
        }
        $http.post(url).success(callback);
    }
    var supervisorStop = function(workflow, callback){
        var url;
        if(workflow){
            url = baseUrl+'/workflows/'+workflow+'/supervisor/stop';
        }
        $http.post(url).success(callback);
    }
    var supervisorStopGracefully = function(workflow, callback){
        var url;
        if(workflow){
            url = baseUrl+'/workflows/'+workflow+'/supervisor/stop_gracefully';
        }
        $http.post(url).success(callback);
    }
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
      supervisorStatus: supervisorStatus,
      supervisorStart: supervisorStart,
      supervisorStop: supervisorStop,
      supervisorStopGracefully: supervisorStopGracefully,
    };
    // AngularJS will instantiate a singleton by calling "new" on this function
  });
