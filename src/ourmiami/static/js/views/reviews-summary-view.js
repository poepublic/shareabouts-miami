/*globals _ Handlebars Backbone */

var Shareabouts = Shareabouts || {};

(function(S, $, console){
  'use strict';

  S.ReviewsSummaryView = Backbone.View.extend({
    events: {
      // 'submit .user-review': 'onFormSubmit'
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

    bindToPlaceReviews: function(model) {
      var collection = model.submissionSets['reviews'];

      if (!collection) {
        collection = models.submissionSets['reviews'] = S.SubmissionCollection(models, {
          submissionType: 'reviews',
          placeModel: model
        });
      }

      collection.on('reset', this.handleChangeReviews, this);
      collection.on('add', this.handleChangeReviews, this);
      collection.on('remove', this.handleChangeReviews, this);
      collection.on('change', this.handleChangeReviews, this);
//      collection.forEach(this.bindToReviewChanges, this);
    },

    unbindFromPlaceReviews: function(model) {
      var collection = model.submissionSets['reviews'];

      if (!collection) return;

      collection.off('reset', this.handleChangeReviews, this);
      collection.off('add', this.handleChangeReviews, this);
      collection.off('remove', this.handleChangeReviews, this);
      collection.off('change', this.handleChangeReviews, this);
      // collection.forEach(this.unbindFromReviewChanges, this);
    },

    bindToReviewChanges: function(model) {
      model.on('change', this.handleChangeReviews, this);
    },

    unbindFromReviewChanges: function(model) {
      model.off('change', this.handleChangeReviews, this);
    },

    // Event handlers
    // ==============

    handleAddPlace: function(model) {
      this.bindToPlaceReviews(model);
      this.updateReviewsDisplays();
    },

    handleRemovePlace: function(model) {
      this.unbindFromPlaceReviews(model);
      this.updateReviewsDisplays();
    },

    handleResetPlaces: function(collection) {
      collection.forEach(this.bindToPlaceReviews, this);
      this.updateReviewsDisplays();
    },

    handleChangeReviews: function(model) {
      this.updateReviewsDisplays();
    },

    // Utility functions
    // =================

    getReviewsCounts: function(reviewOptions, categoryOptions) {
      var total = 0;
      var byReview = {};
      var byReviewCategory = {};
      var userToken = this.options.userToken;
      var seenPlaces = {};

      // Initialize the object for reviews by category.
      reviewOptions.forEach(function(rev) {
        byReview[rev] = 0;
        byReviewCategory[rev] = {};
        categoryOptions.forEach(function(cat) {
          byReviewCategory[rev][cat] = 0;
        });
      });

      // Calculate the total reviews submitted, as well as how
      // many reviews fall into each category (location_type).
      this.collection.forEach(function(place) {
        if (!place.submissionSets['reviews']) return;
        place.submissionSets['reviews'].forEach(function(review) {
          var rev, cat;
          var placeUrl = review.get('place');

          if (review.get('user_token') === userToken) {
            // Get the category and URL of the review.
            cat = place.get('location_type');
            rev = review.get('review');
            if (!rev) return;

            // Each place should only have one review per user. The newest one
            // will be first, so ignore any that we've already seen.
            if (seenPlaces[placeUrl]) { return; }
            seenPlaces[placeUrl] = true;

            // Update the totals
            ++total;
            byReview[rev] += 1;
            byReviewCategory[rev][cat] += 1;
          }
        });
      });

      return {total: total, byReview: byReview, byReviewCategory: byReviewCategory};
    },

    getStaffGroupCount: function(categoryOptions) {
      // NOTE: Remember, unlike ratings, all ideas belong to the same staff group.
      var total = 0;
      var byCategory = {};

      // Initialize the object for places by category.
      categoryOptions.forEach(function(cat) {
        byCategory[cat] = 0;
      });

      this.collection.forEach(function(place) {
        var cat = place.get('location_type');
        ++total;
        byCategory[cat] += 1;
      });
      return {total: total, byCategory: byCategory};
    },

    // UI initial render and update functions
    // ======================================

    render: function() {
      var self = this;
      var reviewLabels = ['Yes', 'Maybe', 'No']
      var reviewOptions = ['yes', 'maybe', 'no'];
      var reviewsConfig = this.options.reviews = _.map(
        _.zip(reviewLabels, reviewOptions),
        function(l_o) { return {label: l_o[0], option: l_o[1]}; }
      );
      var categoriesConfig = this.options.categories;

      // I don't understand why we need to redelegate the event here, but they
      // are definitely unbound after the first render.
      this.delegateEvents();
      this.$el.html(Handlebars.templates['place-list-reviews-summary']());

      // Set up the initial values and templates
      this.initReviewsChart(reviewsConfig, categoriesConfig);

      // Count reviews and projects in each category
      this.updateReviewsDisplays();

      return this;
    },

    updateReviewsDisplays: _.throttle(function() {
      var reviewOptions = _.pluck(this.options.reviews, 'option');
      var categoryOptions = _.pluck(this.options.categories, 'option');
      var reviewsCounts = this.getReviewsCounts(reviewOptions, categoryOptions);
      var staffGroupCount = this.getStaffGroupCount(reviewOptions);

      this.updateReviewsCount(reviewsCounts.total, staffGroupCount.total);
      this.updateReviewsChart(reviewsCounts.byReviewCategory, reviewsCounts.byReview, reviewsCounts.total);
    }, 100),

    // Update the displayed count of completed reviews
    updateReviewsCount: function(countRated, totalToRate) {
      var countTemplate = Handlebars.templates['place-list-reviews-count'];
      this.$el.find('.reviews-count-wrapper').html(countTemplate({
        count: countRated,
        total: totalToRate
      }));
    },

    // Initialize the structure for the reviews stacked bar chart
    initReviewsChart: function(reviewsConfig, categoryConfig) {
      var chartTemplate = Handlebars.templates['place-list-reviews-chart'];
      this.$el.find('.reviews-chart-wrapper').html(chartTemplate({
        reviews: reviewsConfig,
        categories: categoryConfig
      }));
    },

    // Update the reviews counts in the chart; avoid re-rendering the markup so
    // that values can animate.
    //
    // * countByReviewCategory
    //   A 2-dimensional mapping from review-category pair to the number of
    //   ideas that the current user has reviewed in that category with that
    //   review.
    //
    // * countByReview
    //   A mapping from review value to the total number of ideas that the user
    //   has given that review.
    //
    // * countTotal
    //   The total number of ideas that the current user has reviewed.
    //
    updateReviewsChart: function(countByReviewCategory, countByReview, countTotal) {
      var countMax = _.max(_.values(countByReview));

      // Scale the chart appropriately, but in increments so as to not be too
      // jarring
      var scaleFactor = 1.0;
      var tickStep = 3;
           if (countMax > 300) { scaleFactor = 0.05;   tickStep = 60; }
      else if (countMax > 200) { scaleFactor = 0.0667; tickStep = 50; }
      else if (countMax > 80)  { scaleFactor = 0.1;    tickStep = 30; }
      else if (countMax > 60)  { scaleFactor = 0.25;   tickStep = 12; }
      else if (countMax > 40)  { scaleFactor = 0.333;  tickStep = 10; }
      else if (countMax > 30)  { scaleFactor = 0.5;    tickStep = 6; }
      else if (countMax > 20)  { scaleFactor = 0.667;  tickStep = 5; }

      // First resize all of the chart bar segments
      this.$el.find('.reviews-chart-bar').each(function(barIndex, bar) {
        var rat = $(bar).attr('data-review');
        var ratTotal = countByReview[rat];
        var ratShare = 1.0 * ratTotal / countMax;
        $(bar).find('.reviews-chart-segment').each(function(segIndex, segment) {
          var cat = $(segment).attr('data-category');
          var count = countByReviewCategory[rat][cat] || 0;
          $(segment)
            .css('width', (count * scaleFactor) + 'em')
            .attr('title', count + ' ' + $(segment).attr('data-category-label') + ' idea(s) with review of ' + rat)
        });
      });

      // Update the review totals
      this.$el.find('.reviews-chart-review-total').each(function(index, label) {
        var rat = $(label).attr('data-review');
        var ratTotal = countByReview[rat];
        $(label)
          .html(ratTotal ? ratTotal : '');
      });

      // Set the initial margin before the tick labels
      this.$el.find('.reviews-chart-tick-labels-wrapper')
        .css('margin-left', ((tickStep * scaleFactor) / 2.0 + 4.7) + 'em');

      // Set the spacing between tick labels
      this.$el.find('.reviews-chart-tick-label').each(function(labelIndex, label) {
        $(label)
          .html(tickStep * (labelIndex + 1))
          .css('width', (tickStep * scaleFactor * 1.5) + 'em');
      });

      // Set the spacing between ticks
      this.$el.find('.reviews-chart-tick').each(function(tickIndex, tick) {
        $(tick)
          .css('width', (tickStep * scaleFactor) + 'em');
      });
    }
  });

})(Shareabouts, jQuery, Shareabouts.Util.console);
