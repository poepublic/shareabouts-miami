/*globals _ Handlebars Backbone */

var Shareabouts = Shareabouts || {};

(function(S, $, console){
  'use strict';

  S.RatingsSummaryView = Backbone.View.extend({
    events: {
      // 'submit .user-rating': 'onFormSubmit'
    },

    // Initializer
    // ===========

    initialize: function() {
      this.bindToPlaceCollection(this.collection);
    },

    // Event binding & unbinding methods
    // =================================

    bindToPlaceCollection: function(collection) {
      collection.on('reset', this.handleResetPlaces, this);
      collection.on('add', this.handleAddPlace, this);
      collection.on('remove', this.handleRemovePlace, this);
    },

    bindToPlaceRatings: function(model) {
      var collection = model.submissionSets['ratings'];

      if (!collection) {
        collection = models.submissionSets['ratings'] = S.SubmissionCollection(models, {
          submissionType: 'ratings',
          placeModel: model
        });
      }

      collection.on('reset', this.handleChangeRatings, this);
      collection.on('add', this.handleChangeRatings, this);
      collection.on('remove', this.handleChangeRatings, this);
      collection.on('change', this.handleChangeRatings, this);
//      collection.forEach(this.bindToRatingChanges, this);
    },

    unbindFromPlaceRatings: function(model) {
      var collection = model.submissionSets['ratings'];

      if (!collection) return;

      collection.off('reset', this.handleChangeRatings, this);
      collection.off('add', this.handleChangeRatings, this);
      collection.off('remove', this.handleChangeRatings, this);
      collection.off('change', this.handleChangeRatings, this);
      // collection.forEach(this.unbindFromRatingChanges, this);
    },

    bindToRatingChanges: function(model) {
      model.on('change', this.handleChangeRatings, this);
    },

    unbindFromRatingChanges: function(model) {
      model.off('change', this.handleChangeRatings, this);
    },

    // Event handlers
    // ==============

    handleAddPlace: function(model) {
      this.bindToPlaceRatings(model);
      this.updateRatingsDisplays();
    },

    handleRemovePlace: function(model) {
      this.unbindFromPlaceRatings(model);
      this.updateRatingsDisplays();
    },

    handleResetPlaces: function(collection) {
      collection.forEach(this.bindToPlaceRatings, this);
      this.updateRatingsDisplays();
    },

    handleChangeRatings: function(model) {
      this.updateRatingsDisplays();
    },

    // Utility functions
    // =================

    getRatingsCounts: function(ratingOptions, categoryOptions) {
      var total = 0;
      var byRating = {};
      var byRatingCategory = {};
      var userToken = this.options.userToken;

      // Initialize the object for ratings by category.
      ratingOptions.forEach(function(rat) {
        byRating[rat] = 0;
        byRatingCategory[rat] = {};
        categoryOptions.forEach(function(cat) {
          byRatingCategory[rat][cat] = 0;
        });
      });

      // Calculate the total ratings submitted by this user, as well as how
      // many ratings fall into each category (location_type).
      this.collection.forEach(function(place) {
        if (!place.submissionSets['ratings']) return;
        place.submissionSets['ratings'].forEach(function(rating) {
          var rat, cat;

          if (rating.get('user_token') === userToken) {
            cat = place.get('location_type');
            rat = (rating.get('optout') ? 'optout' : rating.get('rating'));
            if (!rat) return;

            ++total;
            byRating[rat] += 1;
            byRatingCategory[rat][cat] += 1;
          }
        });
      });

      return {total: total, byRating: byRating, byRatingCategory: byRatingCategory};
    },

    getJudgeGroupCount: function(categoryOptions) {
      var total = 0;
      var byCategory = {};
      var userJudgeGroups = this.options.userJudgeGroups;

      // Initialize the object for places by category.
      categoryOptions.forEach(function(cat) {
        byCategory[cat] = 0;
      });

      this.collection.forEach(function(place) {
        var cat;
        if (_.contains(userJudgeGroups, place.get('judgeGroup'))) {
          cat = place.get('location_type');

          ++total;
          byCategory[cat] += 1;
        }
      });
      return {total: total, byCategory: byCategory};
    },

    // UI initial render and update functions
    // ======================================

    render: function() {
      var self = this;
      var ratingOptions = [1, 2, 3, 4, 5, 'optout'];
      var categoryOptions = this.options.categories;

      // I don't understand why we need to redelegate the event here, but they
      // are definitely unbound after the first render.
      this.delegateEvents();
      this.$el.html(Handlebars.templates['place-list-ratings-summary']());

      // Set up the initial values and templates
      this.initRatingsChart(ratingOptions, categoryOptions);

      // Count ratings and projects in each category
      this.updateRatingsDisplays();

      return this;
    },

    updateRatingsDisplays: _.throttle(function() {
      var ratingOptions = [1, 2, 3, 4, 5, 'optout'];
      var categoryOptions = this.options.categories;
      var ratingsCounts = this.getRatingsCounts(ratingOptions, categoryOptions);
      var judgeGroupCount = this.getJudgeGroupCount(ratingOptions);

      this.updateRatingsCount(ratingsCounts.total, judgeGroupCount.total);
      this.updateRatingsChart(ratingsCounts.byRatingCategory, ratingsCounts.byRating, ratingsCounts.total);
    }, 100),

    // Update the displayed count of completed ratings
    updateRatingsCount: function(countRated, totalToRate) {
      var countTemplate = Handlebars.templates['place-list-ratings-count'];
      this.$el.find('.ratings-count-wrapper').html(countTemplate({
        count: countRated,
        total: totalToRate
      }));
    },

    // Initialize the structure for the ratings stacked bar chart
    initRatingsChart: function(ratingOptions, categoryOptions) {
      var chartTemplate = Handlebars.templates['place-list-ratings-chart'];
      this.$el.find('.ratings-chart-wrapper').html(chartTemplate({
        ratingOptions: ratingOptions,
        categoryOptions: categoryOptions
      }));
    },

    // Update the ratings counts in the chart; avoid re-rendering the markup so
    // that values can animate.
    //
    // * countByRatingCategory
    //   A 2-dimensional mapping from rating-category pair to the number of
    //   ideas that the current user has judged in that category with that
    //   rating.
    //
    // * countByRating
    //   A mapping from rating value to the total number of ideas that the user
    //   has given that rating.
    //
    // * countTotal
    //   The total number of ideas that the current user has judged.
    //
    updateRatingsChart: function(countByRatingCategory, countByRating, countTotal) {
      var countMax = _.max(_.values(countByRating));
      if (!countMax) return;

      this.$el.find('.ratings-chart-bars').each(function(barIndex, bar) {
        var rat = $(bar).attr('data-rating');
        var ratTotal = countByRating[rat];
        var ratShare = 1.0 * ratTotal / countMax;
        $(bar).find('.ratings-chart-segment').each(function(segIndex, segment) {
          var cat = $(segment).attr('data-category');
          var value = countByRatingCategory[rat][cat] || 0;
          $(segment).css('width', (ratTotal ? value * 100.0 / ratTotal * ratShare : 0) + '%');
        });
      });
    }
  });

})(Shareabouts, jQuery, Shareabouts.Util.console);
