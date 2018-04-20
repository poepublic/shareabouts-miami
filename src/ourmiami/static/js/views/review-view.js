/*globals _ Handlebars Backbone */

var Shareabouts = Shareabouts || {};

(function(S, $, console){
  'use strict';

  S.ReviewView = Backbone.View.extend({
    events: {
      'change .evaluation': 'onEvaluationChange',
      'change input[name=review_notes]': 'onReviewChange',
      'submit .user-review': 'onFormSubmit'
    },

    initialize: function() {
      this.collection.on('reset', this.onChange, this);
      this.collection.on('add', this.onChange, this);
      this.collection.on('remove', this.onChange, this);
    },

    render: function() {
      var self = this,
          userReview,

          // The userStaffGroup is set in an app initializer in index.html
          // NOTE: Treat all places as being in the current staff group
          userStaffGroup = S.Config.userStaffGroup;

      if (!userStaffGroup || !userStaffGroup.length) {
        return this;
      }

      // I don't understand why we need to redelegate the events here, but they
      // are definitely unbound after the first render.
      this.delegateEvents();

      // NOTE: All reviews use modify the same reviews
      userReview = this.getReview();
      this.$el.html(Handlebars.templates['place-detail-review']({
        count: this.collection.size() || '',
        user_token: this.options.userToken,
        user_review: userReview.toJSON(),
        place_id: this.collection.options.placeModel.id
      }));

      return this;
    },

    remove: function() {
      // Nothing yet
    },

    unbindReview: function() {
      if (this.userReview) { this.userReview.off('change', this.onChange, this); }
    },
    bindReview: function() {
      if (this.userReview) { this.userReview.on('change', this.onChange, this); }
    },

    getReview: function() {
      var userToken = this.options.userToken,
          reviews = this.collection,
          ReviewModel = reviews.model,
          model = this.collection.findWhere({'user_token': userToken});

      if (!this.userReview || (model && this.userReview !== model)) {
        this.unbindReview();
        this.userReview = model || new ReviewModel();
        this.bindReview();
      }

      if (this.userReview.isNew()) {
        this.userReview.urlRoot = reviews.url();
      }

      return this.userReview;
    },

    onChange: function() {
      this.render();
    },

    onFormSubmit: function(evt) {
      evt.preventDefault();
      this.saveReview();
    },

    onReviewNotesBlur: function(evt) {
      var userReview = this.getReview(),
          oldNotes = userReview.get('review_notes'),
          newNotes = $(evt.currentTarget).val();

      if (newNotes !== oldNotes) {
        this.saveReview();
      }
    },

    onEvaluationChange: function(evt) {
      if (evt.target.checked) {
        var review = evt.target.getAttribute('data-review-value');

        S.Util.log('USER', 'place', 'review-btn-click', this.collection.options.placeModel.getLoggingDetails(), review);
        this.saveReview();
      }
    },

    onReviewChange: function(evt) {
      this.saveReview();
    },

    saveReview: function() {
      var self = this,
          evalButtons = this.el.getElementsByClassName('evaluation'),
          notesWidget = $('[name=review_notes]'),
          $form, attrs,
          reviews = this.collection,
          ReviewModel = reviews.model,
          userReview = this.getReview();

      // Disable the evaluation widgets while we save; they'll be enabled again on complete
      // _.map(evalButtons, function(button) { button.disabled = true; });
      // notesWidget.each(function(i, widget) { widget.disabled = false; });

      $form = this.$('form');
      attrs = S.Util.getAttrs($form);

      userReview.save(attrs, {
        wait: true,
        beforeSend: function(xhr) {
          // Set the silent header so that review doesn't generate activity
          xhr.setRequestHeader('X-Shareabouts-Silent', 'true');
        },
        complete: function() {
          _.map(evalButtons, function(button) { button.disabled = false; });
          notesWidget.each(function(i, widget) { widget.disabled = false; });
        },
        success: function() {
          reviews.add(userReview);
          S.Util.log('USER', 'place', 'successfully-review', self.collection.options.placeModel.getLoggingDetails());
        },
        error: function() {
          alert('Oh dear. It looks like that didn\'t save.');
          S.Util.log('USER', 'place', 'fail-to-review', self.collection.options.placeModel.getLoggingDetails());
        }
      });
    }
  });

})(Shareabouts, jQuery, Shareabouts.Util.console);
